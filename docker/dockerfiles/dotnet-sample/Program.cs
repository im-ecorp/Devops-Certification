var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => Results.Ok(new { message = "Hello from .NET in Docker!" }));
app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.Run();
