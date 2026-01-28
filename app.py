from pathlib import Path
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cv2
import numpy as np
import json
import os
import threading
import time
import asyncio
from typing import Optional, Dict, Any, List
import uvicorn
from calibration import CameraCalibrator
import io
import time
from PIL import Image, ImageDraw, ImageFont
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--camera", default=0, type=str, help="camera name to caliberate")
parser.add_argument("--port", default=5000, type=int, help="port to run the server")
args = parser.parse_args()

app = FastAPI(title="摄像头自动标定系统", version="1.0.0")

# 添加CORS中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
calibrator = CameraCalibrator()
is_calibrating = False
calibration_progress = 0
calibration_message = ""
calibration_results = {}
camera = None
chessboard_size = (9, 6)  # 默认棋盘格尺寸
camera_lock = threading.Lock()  # 摄像头访问锁


# Pydantic模型
class ChessboardSize(BaseModel):
    chessboard_width: int
    chessboard_height: int
    square_size: float


class CalibrationResponse(BaseModel):
    status: str
    message: str
    chessboard_size: Optional[List[int]] = None


# 初始化摄像头
def init_camera():
    """初始化摄像头"""
    global camera
    with camera_lock:
        if camera is None or not camera.isOpened():
            try:
                try:
                    args.camera = int(args.camera)
                except Exception:
                    pass
                camera = cv2.VideoCapture(args.camera)
                if not camera.isOpened():
                    print(f"Can't open camera {args.camera}")
                    exit(-1)

                if camera.isOpened():
                    # 设置摄像头分辨率
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    camera.set(cv2.CAP_PROP_FPS, 30)
                    print(f"摄像头已初始化: 分辨率 640x480")
                else:
                    print("警告: 无法打开摄像头，将使用模拟帧")

            except Exception as e:
                print(f"初始化摄像头时出错: {e}")
                camera = None
    return camera


def calibration_thread(
    chessboard_width: int, chessboard_height: int, square_size: float
):
    """标定线程"""
    global is_calibrating, calibration_progress, calibration_message, calibration_results, chessboard_size

    try:
        # 设置棋盘格尺寸
        chessboard_size = (chessboard_width, chessboard_height, square_size)

        # 重置标定器并设置新的棋盘格尺寸
        calibrator.reset()
        calibrator.set_chessboard_size(chessboard_width, chessboard_height, square_size)

        # 开始标定过程
        cam = init_camera()

        if cam is None or not cam.isOpened():
            calibration_message = "摄像头未连接，请检查摄像头连接"
            calibration_progress = 0
            is_calibrating = False
            return

        results = calibrator.auto_calibrate(
            camera=cam,
            progress_callback=lambda p, m: update_progress(p, m),
            max_images=30,
            min_images=15,
        )

        calibration_results = results
        calibration_progress = 100
        calibration_message = "标定完成！"

        # 保存标定结果
        save_calibration_results(results)

    except Exception as e:
        calibration_message = f"标定失败: {str(e)}"
        print(f"标定过程中出错: {e}")
    finally:
        is_calibrating = False


def update_progress(progress: int, message: str):
    """更新标定进度"""
    global calibration_progress, calibration_message
    calibration_progress = progress
    calibration_message = message


def save_calibration_results(results: Dict[str, Any]):
    """保存标定结果到文件"""
    if not os.path.exists("calibration_results"):
        os.makedirs("calibration_results")

    try:
        # 保存为JSON
        with open("calibration_results/calibration.json", "w") as f:
            json.dump(
                {
                    "camera_matrix": results["camera_matrix"].tolist(),
                    "dist_coeffs": results["dist_coeffs"].tolist(),
                    "reprojection_error": results["reprojection_error"],
                    "calibration_images": results["calibration_images"],
                    "chessboard_size": results["chessboard_size"],
                },
                f,
                indent=2,
            )

        # 保存为NumPy格式
        np.savez(
            "calibration_results/calibration.npz",
            camera_matrix=results["camera_matrix"],
            dist_coeffs=results["dist_coeffs"],
        )

        # 保存为文本格式便于查看
        with open("calibration_results/calibration.txt", "w") as f:
            f.write("相机标定结果\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"棋盘格尺寸: {results['chessboard_size']}\n")
            f.write(f"标定图片数量: {results['calibration_images']}\n")
            f.write(f"重投影误差: {results['reprojection_error']:.6f}\n\n")
            f.write("相机矩阵:\n")
            np.savetxt(f, results["camera_matrix"], fmt="%10.5f")
            f.write("\n畸变系数:\n")
            np.savetxt(f, results["dist_coeffs"], fmt="%10.5f")

        print("标定结果已保存到 calibration_results/ 目录")

    except Exception as e:
        print(f"保存标定结果时出错: {e}")


def generate_frames():
    """生成视频流"""
    cam = init_camera()

    if cam is None or not cam.isOpened():
        raise ValueError("相机不可用")

    while True:
        try:
            with camera_lock:
                success, frame = cam.read()
                if not success:
                    print("摄像头读取失败")
                    continue

            # 如果正在标定，在帧上绘制检测结果
            if is_calibrating:
                frame = calibrator.draw_corners(frame)

            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = buffer.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

            # 控制帧率
            time.sleep(0.033)  # 约30fps

        except Exception as e:
            print(f"生成视频帧时出错: {e}")
            time.sleep(1)
            continue


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    print("摄像头自动标定系统启动中...")
    # 初始化摄像头
    init_camera()
    # 确保标定结果目录存在
    os.makedirs("calibration_results", exist_ok=True)
    os.makedirs("static", exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global camera
    with camera_lock:
        if camera is not None:
            camera.release()
            camera = None
            print("摄像头已释放")


@app.get("/")
async def read_root():
    """返回前端页面"""
    return FileResponse(static_dir.joinpath("index.html"))


@app.get("/video_feed")
async def video_feed():
    """视频流端点"""
    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.post("/start_calibration")
async def start_calibration(size: ChessboardSize):
    """开始标定"""
    global is_calibrating

    if is_calibrating:
        raise HTTPException(status_code=400, detail="标定正在进行中")

    # 验证棋盘格尺寸
    if size.chessboard_width < 3 or size.chessboard_height < 3:
        raise HTTPException(status_code=400, detail="棋盘格尺寸至少为3x3")

    if size.chessboard_width > 15 or size.chessboard_height > 15:
        raise HTTPException(status_code=400, detail="棋盘格尺寸最大为15x15")

    is_calibrating = True
    calibration_thread_instance = threading.Thread(
        target=calibration_thread,
        args=(size.chessboard_width, size.chessboard_height, size.square_size),
    )
    calibration_thread_instance.daemon = True
    calibration_thread_instance.start()

    return JSONResponse(
        {
            "status": "success",
            "message": f"开始标定，棋盘格尺寸: {size.chessboard_width}x{size.chessboard_height}",
        }
    )


@app.post("/stop_calibration")
async def stop_calibration():
    """停止标定"""
    global is_calibrating
    is_calibrating = False
    calibrator.stop_calibration = True
    return JSONResponse({"status": "success", "message": "停止标定"})


@app.post("/update_chessboard_size")
async def update_chessboard_size(size: ChessboardSize):
    """更新棋盘格尺寸"""
    global chessboard_size, is_calibrating, calibration_progress, calibration_message, calibration_results

    if is_calibrating:
        raise HTTPException(status_code=400, detail="标定正在进行中，请先停止标定")

    # 验证棋盘格尺寸
    if size.chessboard_width < 3 or size.chessboard_height < 3:
        raise HTTPException(status_code=400, detail="棋盘格尺寸至少为3x3")

    if size.chessboard_width > 15 or size.chessboard_height > 15:
        raise HTTPException(status_code=400, detail="棋盘格尺寸最大为15x15")

    # 更新棋盘格尺寸
    chessboard_size = (size.chessboard_width, size.chessboard_height, size.square_size)

    # 重置标定器
    calibrator.reset()
    calibrator.set_chessboard_size(
        size.chessboard_width, size.chessboard_height, size.square_size
    )

    # 重置标定状态
    calibration_progress = 0
    calibration_message = f"棋盘格尺寸已更新为 {size.chessboard_width}x{size.chessboard_height}，请重新开始标定"
    calibration_results = {}

    return JSONResponse(
        {
            "status": "success",
            "message": f"棋盘格尺寸已更新为: {size.chessboard_width}x{size.chessboard_height}",
            "chessboard_size": list(chessboard_size),
        }
    )


@app.get("/get_calibration_status")
async def get_calibration_status():
    """获取标定状态"""
    global is_calibrating, calibration_progress, calibration_message, calibration_results, chessboard_size

    response = {
        "is_calibrating": is_calibrating,
        "progress": calibration_progress,
        "message": calibration_message,
        "has_results": len(calibration_results) > 0,
        "chessboard_size": list(chessboard_size),
    }

    if calibration_results:
        response.update(
            {
                "camera_matrix": calibration_results["camera_matrix"].tolist(),
                "dist_coeffs": calibration_results["dist_coeffs"].flatten().tolist(),
                "reprojection_error": float(calibration_results["reprojection_error"]),
                "num_images": calibration_results["calibration_images"],
                "chessboard_size": calibration_results.get(
                    "chessboard_size", list(chessboard_size)
                ),
            }
        )

    return JSONResponse(response)


@app.get("/get_calibration_results")
async def get_calibration_results():
    """获取标定结果"""
    if os.path.exists("calibration_results/calibration.json"):
        with open("calibration_results/calibration.json", "r") as f:
            results = json.load(f)
        return JSONResponse({"status": "success", "results": results})
    else:
        raise HTTPException(status_code=404, detail="未找到标定结果")


@app.post("/reset_calibration")
async def reset_calibration():
    """重置标定"""
    global is_calibrating, calibration_progress, calibration_message, calibration_results, chessboard_size
    is_calibrating = False
    calibrator.stop_calibration = True
    calibration_progress = 0
    calibration_message = "标定已重置"
    calibration_results = {}
    chessboard_size = (9, 6)  # 重置为默认值
    calibrator.reset()
    calibrator.set_chessboard_size(9, 6)  # 重置为默认尺寸

    return JSONResponse({"status": "success", "message": "标定已重置"})


@app.get("/get_chessboard_size")
async def get_chessboard_size():
    """获取当前棋盘格尺寸"""
    global chessboard_size
    return JSONResponse({"status": "success", "chessboard_size": list(chessboard_size)})


static_dir = Path(__file__).parent.joinpath("app", "dist")
# 提供静态文件服务（用于前端文件）
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")
