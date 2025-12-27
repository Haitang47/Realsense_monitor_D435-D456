import pyrealsense2 as rs
import numpy as np
import cv2
from flask import Flask, Response, render_template_string
import threading
import time
import os

app = Flask(__name__)

# 配置参数
SAVE_PATH = "./recordings"
if not os.path.exists(SAVE_PATH): os.makedirs(SAVE_PATH)

class CameraServer:
    def __init__(self):
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.pipeline.start(config)
        
        # 录制设置
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        filename = os.path.join(SAVE_PATH, f"rec_{time.strftime('%Y%m%d_%H%M%S')}.mkv")
        self.out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        
        self.current_frame = None

    def capture_loop(self):
        try:
            while True:
                frames = self.pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                if not color_frame: continue
                
                # 转换图像
                frame = np.asanyarray(color_frame.get_data())
                self.current_frame = frame
                
                # 写入本地文件
                self.out.write(frame)
        finally:
            self.pipeline.stop()
            self.out.release()

cam = CameraServer()

def gen_frames():
    while True:
        if cam.current_frame is not None:
            # 编码为 JPEG 格式用于网页传输
            ret, buffer = cv2.imencode('.jpg', cam.current_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.04) # 限制约 25 FPS 减轻 CPU 负担

@app.route('/')
def index():
    return render_template_string('<html><body><h1>RealSense D456 Live</h1><img src="{{ url_for(\'video_feed\') }}" width="100%"></body></html>')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # 启动抓图线程
    t = threading.Thread(target=cam.capture_loop)
    t.daemon = True
    t.start()
    # 启动 Web 服务 (0.0.0.0 允许局域网访问)
    app.run(host='0.0.0.0', port=5000, threaded=True)
