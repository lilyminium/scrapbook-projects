

```
IMAGE_NAME='tmp-evaluator-openeye-kubernetes-v0'
docker build --platform linux/amd64 --tag $IMAGE_NAME .
docker tag $IMAGE_NAME "ghcr.io/lilyminium/scrapbook-projects:${IMAGE_NAME}"
docker push "ghcr.io/lilyminium/scrapbook-projects:${IMAGE_NAME}"
```

