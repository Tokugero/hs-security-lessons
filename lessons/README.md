# TLDR on making containers:

```
cd <lessonpath>
docker build -t <imagename> .
docker run --rm -it -p 3390:3389 -p 5900:5900 <imagename>
```
