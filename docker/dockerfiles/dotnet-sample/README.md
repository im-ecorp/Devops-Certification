# .NET: a minimal ASP.NET Core API

An original minimal API using .NET 10 and official Microsoft images. It follows
Microsoft's separate restore/publish/runtime pattern without copying its larger
Razor application. The existing `dotnet-sample/` folder name is retained.

## Why this example

Docker's [.NET sample](https://github.com/docker/docker-dotnet-sample) is a useful
Razor Pages app targeting .NET 10, but has no checked-in Dockerfile at review time.
Microsoft's [dotnet-docker samples](https://github.com/dotnet/dotnet-docker/tree/main/samples)
are a better Dockerfile reference: runtime-only stages, non-root users, multi-platform
builds, chiseled images, globalization, native AOT, and multi-project tests.
Its current `main` Razor sample uses .NET 11 image tags; this lab deliberately uses
.NET 10 rather than copying that version blindly.

This API makes caching and the SDK/runtime distinction easy to see. Learn this
first, then explore Microsoft's [Razor sample](https://github.com/dotnet/dotnet-docker/tree/main/samples/AspNetCoreRazorApp)
and advanced image variants. Chiseled images remove shell/package tooling and need
more care with diagnostics and globalization; they are not necessary for a first lab.

## Files and Dockerfile

- `DockerLearningApi.csproj`: targets `net10.0`; only the ASP.NET shared framework,
  no third-party package references.
- `Program.cs`: `/` returns a greeting; `/health` returns `{"status":"ok"}`.
- SDK stage: copies the project file, runs `dotnet restore`, then copies source.
  Code-only edits can reuse the restore layer. With a larger solution, copy all
  restore inputs first, including project references, NuGet configuration, and
  central package files.
- `dotnet publish -c Release --no-restore`: produces deployment files without
  restoring twice. `/p:UseAppHost=false` avoids a platform-specific native launcher;
  the runtime starts the DLL through `dotnet`.
- Runtime stage: `mcr.microsoft.com/dotnet/aspnet:10.0` contains the ASP.NET runtime,
  not the full SDK. Only `/out` is copied across.
- `USER $APP_UID`: selects the built-in non-root user from Microsoft's image.
  Port 8080 needs no privileged port access. Runtime files remain root-owned/readable.
- `ASPNETCORE_HTTP_PORTS=8080` and `EXPOSE 8080`: set and document the container port.
- Exec-form `ENTRYPOINT`: starts the application directly in the foreground.
- `.dockerignore` and `.gitignore`: exclude local `bin/`, `obj/`, caches, and secrets.

No image-level health check is added because curl is not needed by the application.
The `/health` endpoint supports an external probe; it only checks the process,
not databases or other dependencies.

## Build and run

Prerequisites: Docker with a running daemon and access to Microsoft's container registry.
Docker builds do not require a .NET SDK on the host. From the repository root:

```bash
cd docker/dockerfiles/dotnet-sample
docker build -t learn-dotnet .
docker run --rm -p 127.0.0.1:8081:8080 learn-dotnet
```

Port 8081 on the host avoids the static-site lab's default host port. In another terminal:

```bash
curl -f http://127.0.0.1:8081/
curl -f http://127.0.0.1:8081/health
```

Expected: `{"message":"Hello from .NET in Docker!"}` and `{"status":"ok"}`.
Stop with Ctrl+C. `--rm` removes this disposable container.

## Test without Docker

Prerequisites: .NET 10 SDK and Python 3, from this example directory:

```bash
dotnet build DockerLearningApi.csproj
python3 -m unittest -v test_http.py
dotnet publish DockerLearningApi.csproj -c Release --no-restore /p:UseAppHost=false
```

The smoke test starts the built app on an ephemeral localhost port and checks
both endpoints and 404 behavior. It tests the app, not the container image.

## Verify and experiment

```bash
docker run --rm --entrypoint id learn-dotnet
docker run --rm --entrypoint dotnet learn-dotnet --list-runtimes
docker run --rm --entrypoint dotnet learn-dotnet --list-sdks
docker build --target build -t learn-dotnet-builder .
docker image ls learn-dotnet
docker image ls learn-dotnet-builder
```

Expect a non-root user, installed runtimes, and no SDK listed in the final image.
Actual image sizes depend on platform and updates. Edit only `Program.cs` and
rebuild with `--progress=plain` to observe the cached restore step.

This is a Linux-container example, not .NET Framework/Windows containers. It is
stateless and uses plain HTTP for localhost practice. Production needs security
review, patched base images, digest pinning where required, logging/resource
controls, and appropriate TLS handling. Match target framework and image runtime versions.

Sources: [Microsoft ASP.NET container guide](https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/docker/building-net-docker-images?view=aspnetcore-10.0),
[Microsoft container samples](https://github.com/dotnet/dotnet-docker/tree/main/samples),
[Non-root image users](https://learn.microsoft.com/en-us/dotnet/core/docker/introduction).

[Back to labs](../README.md)
