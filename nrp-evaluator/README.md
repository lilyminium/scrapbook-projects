

```
docker build --platform linux/amd64 --tag tmp-evaluator-openeye-v0 .
```


```
docker run -it -p 8000:8000 --platform linux/amd64 tmp-evaluator-openeye-v0
```