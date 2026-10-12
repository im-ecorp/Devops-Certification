using System;
using System.Data.Common;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Npgsql;
using StackExchange.Redis;

namespace Worker
{
    public class Program
    {
        private const string DatabaseConnection = "Host=db;Username=postgres;Password=postgres;";
        private const string RedisHost = "redis";

        public static async Task<int> Main(string[] args)
        {
            using var shutdown = new CancellationTokenSource();
            Console.CancelKeyPress += (_, e) => { e.Cancel = true; shutdown.Cancel(); };
            try
            {
                await RunAsync(shutdown.Token);
                return 0;
            }
            catch (OperationCanceledException) when (shutdown.IsCancellationRequested)
            {
                return 0;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex);
                return 1;
            }
        }

        private static async Task RunAsync(CancellationToken token)
        {
            using var connection = new NpgsqlConnection(DatabaseConnection);
            await OpenDatabaseAsync(connection, token);
            using var redisConnection = await OpenRedisAsync(token);
            var redis = redisConnection.GetDatabase();
            await RunVoteLoopAsync(
                async cancellation => (string)await redis.ListLeftPopAsync("votes").WaitAsync(cancellation),
                async (id, vote, cancellation) =>
                {
                    if (connection.State != System.Data.ConnectionState.Open)
                        await OpenDatabaseAsync(connection, cancellation);
                    using var command = CreateVoteCommand(connection, id, vote);
                    await command.ExecuteNonQueryAsync(cancellation);
                }, Console.Error.WriteLine, token);
        }

        // Only the external read/write boundary is injected; parsing, retries and cancellation
        // are the same code used by the real worker and the database-free tests.
        public static async Task RunVoteLoopAsync(
            Func<CancellationToken, Task<string>> read,
            Func<string, string, CancellationToken, Task> write,
            Action<string> log, CancellationToken token)
        {
            var definition = new { vote = "", voter_id = "" };
            while (true)
            {
                token.ThrowIfCancellationRequested();
                // Redis pop is not transactional with Postgres; this remains a demo queue.
                string json;
                try
                {
                    json = await read(token);
                }
                catch (RedisException ex)
                {
                    log($"Redis unavailable: {ex.Message}");
                    await Task.Delay(1000, token);
                    continue; // Multiplexer reconnects in the background.
                }

                if (json == null)
                {
                    await Task.Delay(100, token);
                    continue;
                }

                try
                {
                var vote = JsonConvert.DeserializeAnonymousType(json, definition);
                if (vote == null || string.IsNullOrEmpty(vote.voter_id) || string.IsNullOrEmpty(vote.vote))
                {
                    Console.Error.WriteLine("Ignoring invalid vote payload");
                    continue;
                }
                Console.WriteLine($"Processing vote for '{vote.vote}' by '{vote.voter_id}'");
                try
                {
                    await write(vote.voter_id, vote.vote, token);
                }
                catch (DbException ex)
                {
                    // Do not turn a database outage into a fake duplicate-voter update.
                    // Redis already popped this payload; see README's delivery limitation.
                    Console.Error.WriteLine($"Database write failed: {ex}");
                    await Task.Delay(1000, token);
                }
                }
                catch (JsonException ex)
                {
                    log($"Ignoring malformed vote payload: {ex.Message}");
                }
            }
        }

        private static async Task OpenDatabaseAsync(NpgsqlConnection connection, CancellationToken token)
        {
            while (true)
            {
                try
                {
                    if (connection.State != System.Data.ConnectionState.Closed)
                        await connection.CloseAsync();
                    await connection.OpenAsync(token);
                    using var command = connection.CreateCommand();
                    command.CommandText = @"CREATE TABLE IF NOT EXISTS votes (
                        id VARCHAR(255) NOT NULL UNIQUE,
                        vote VARCHAR(255) NOT NULL
                    )";
                    await command.ExecuteNonQueryAsync(token);
                    Console.Error.WriteLine("Connected to db");
                    return;
                }
                catch (DbException ex)
                {
                    Console.Error.WriteLine($"Waiting for db: {ex.Message}");
                    await Task.Delay(1000, token);
                }
            }
        }

        private static async Task<ConnectionMultiplexer> OpenRedisAsync(CancellationToken token)
        {
            while (true)
            {
                try
                {
                    // DNS hostname is handled by the supported Redis client; no IPv4-only lookup.
                    var options = ConfigurationOptions.Parse(RedisHost);
                    options.AbortOnConnectFail = false;
                    var connection = await ConnectionMultiplexer.ConnectAsync(options);
                    Console.Error.WriteLine("Connected to redis");
                    return connection;
                }
                catch (RedisConnectionException ex)
                {
                    Console.Error.WriteLine($"Waiting for redis: {ex.Message}");
                    await Task.Delay(1000, token);
                }
            }
        }

        // A pure command-construction seam for a database-free regression test.
        public static NpgsqlCommand CreateVoteCommand(NpgsqlConnection connection, string voterId, string vote)
        {
            var command = connection.CreateCommand();
            command.CommandText = @"INSERT INTO votes (id, vote) VALUES (@id, @vote)
                ON CONFLICT (id) DO UPDATE SET vote = EXCLUDED.vote";
            command.Parameters.AddWithValue("id", voterId);
            command.Parameters.AddWithValue("vote", vote);
            return command;
        }
    }
}
