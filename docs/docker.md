docker builder prune
docker build -t mnemo_v1-0 .
docker save -o mnemo_v1-0.tar mnemo_v1-0:latest
docker load -i my_app_image.tar
docker images
docker run -p 8501:8501 -v /Users:/Users test1_streamlit_app