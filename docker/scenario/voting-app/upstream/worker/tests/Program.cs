using System;
using System.Threading.Tasks;
using Npgsql;
using Worker;

// Real command construction, no database or Redis service is present on this host.
using var connection = new NpgsqlConnection("Host=localhost;Username=postgres;Password=postgres");
using var command = Worker.Program.CreateVoteCommand(connection, "voter-1", "a");
if (!command.CommandText.Contains("ON CONFLICT (id) DO UPDATE", StringComparison.Ordinal))
    throw new Exception("A duplicate voter must update via an atomic upsert, not a catch-all exception");
if (!command.CommandText.Contains("EXCLUDED.vote", StringComparison.Ordinal))
    throw new Exception("Upsert must use the new vote");
if ((string)command.Parameters["id"].Value != "voter-1" || (string)command.Parameters["vote"].Value != "a")
    throw new Exception("Vote values must be bound as parameters");
Console.WriteLine("PASS: parameterized single-statement vote upsert");

using var cancelled = new System.Threading.CancellationTokenSource();
cancelled.Cancel();
int reads = 0;
try
{
    await Worker.Program.RunVoteLoopAsync(
        token => { reads++; return Task.FromResult<string>(null); },
        (id, vote, token) => Task.CompletedTask,
        _ => { }, cancelled.Token);
}
catch (OperationCanceledException) { }
if (reads != 0) throw new Exception("Cancelled worker must not dequeue a vote");
Console.WriteLine("PASS: cancellation prevents dequeue");

using var stop = new System.Threading.CancellationTokenSource();
int writes = 0;
string writtenId = null;
await Worker.Program.RunVoteLoopAsync(
    token => Task.FromResult("{\"voter_id\":\"repeat-voter\",\"vote\":\"b\"}"),
    (id, vote, token) => { writes++; writtenId = id; if (vote != "b") throw new Exception("Wrong vote"); stop.Cancel(); return Task.CompletedTask; },
    _ => { }, stop.Token).ContinueWith(task => {
        if (!task.IsCanceled) throw new Exception("Loop must observe cancellation after a write");
    });
if (writes != 1 || writtenId != "repeat-voter") throw new Exception("Parsed vote must be written once");
Console.WriteLine("PASS: parsed vote reaches the database write boundary once");

using var invalidStop = new System.Threading.CancellationTokenSource();
int invalidReads = 0;
int invalidWrites = 0;
await Worker.Program.RunVoteLoopAsync(
    token => { if (invalidReads++ == 0) return Task.FromResult("not-json"); invalidStop.Cancel(); return Task.FromCanceled<string>(invalidStop.Token); },
    (id, vote, token) => { invalidWrites++; return Task.CompletedTask; },
    _ => { }, invalidStop.Token).ContinueWith(task => {
        if (!task.IsCanceled) throw new Exception("Invalid JSON must be skipped without killing the worker", task.Exception);
    });
if (invalidWrites != 0) throw new Exception("Malformed message must not reach the database");
Console.WriteLine("PASS: malformed JSON is skipped without a database write");
