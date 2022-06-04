all() {
docker build -t frontend -f dockerfiles/frontend.dockerfile .
docker build -t base --platform linux/x86_64 -f dockerfiles/base.dockerfile .
docker build -t library --platform linux/x86_64 -f dockerfiles/library.dockerfile .
docker build -t ocr --platform linux/x86_64 -f dockerfiles/ocr.dockerfile .
docker build -t text_detector --platform linux/x86_64 -f dockerfiles/text_detector.dockerfile .
}

services() {
  docker build -t library --platform linux/x86_64 -f dockerfiles/library.dockerfile .
  docker build -t ocr --platform linux/x86_64 -f dockerfiles/ocr.dockerfile .
  docker build -t text_detector --platform linux/x86_64 -f dockerfiles/text_detector.dockerfile .
}

frontend() {
  docker build -t frontend -f dockerfiles/frontend.dockerfile .
}

base() {
 docker build -t base --platform linux/x86_64 -f dockerfiles/base.dockerfile . 
}