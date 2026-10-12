#!/bin/sh
# Build from maintained sibling source; do not duplicate or change the Compose lab.
set -eu
: "${IMAGE_PREFIX:?Export IMAGE_PREFIX, e.g. ghcr.io/your-account/swarm-voting}"
: "${IMAGE_TAG:?Export IMAGE_TAG, e.g. a Git revision}"
: "${PLATFORM:=linux/amd64}"
case "$IMAGE_PREFIX" in *://*|*' '*|'') echo "IMAGE_PREFIX must be a registry repository prefix, not a URL" >&2; exit 1;; esac
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE="$HERE/../../scenario/voting-app/upstream"
for component in vote result worker; do
  test -f "$SOURCE/$component/Dockerfile"
  if [ "$component" = vote ]; then
    docker buildx build --platform "$PLATFORM" --target final --push \
      -t "$IMAGE_PREFIX-$component:$IMAGE_TAG" "$SOURCE/$component"
  else
    docker buildx build --platform "$PLATFORM" --push \
      -t "$IMAGE_PREFIX-$component:$IMAGE_TAG" "$SOURCE/$component"
  fi
done
printf 'Built and pushed vote, result and worker for %s.\n' "$PLATFORM"
