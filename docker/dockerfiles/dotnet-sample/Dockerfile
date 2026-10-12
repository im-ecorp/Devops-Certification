# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
# Restore before copying source so code-only edits reuse this layer.
COPY DockerLearningApi.csproj ./
RUN dotnet restore DockerLearningApi.csproj
COPY Program.cs ./
RUN dotnet publish DockerLearningApi.csproj -c Release -o /out --no-restore /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app
COPY --from=build /out/ ./
ENV ASPNETCORE_HTTP_PORTS=8080
USER $APP_UID
EXPOSE 8080
ENTRYPOINT ["dotnet", "DockerLearningApi.dll"]
