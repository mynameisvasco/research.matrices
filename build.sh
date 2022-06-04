docker build -t frontend:latest -f dockerfiles/frontend.dockerfile .
docker build -t base:latest --platform linux/x86_64 -f dockerfiles/base.dockerfile .
docker build -t library:latest -f dockerfiles/library.dockerfile .
docker build -t ocr:latest -f dockerfiles/ocr.dockerfile .
docker build -t text_detector:latest -f dockerfiles/text_detector.dockerfile .