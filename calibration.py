# -*- coding: utf-8 -*-
import math
import cv2
import numpy as np
import time
from typing import List, Optional, Callable, Dict, Any, Tuple
import threading
from dataclasses import dataclass, fields
import json


@dataclass
class CalibrationResults:
    camera_matrix: np.ndarray
    dist_coeffs: np.ndarray
    rvecs: List[Any]
    tvecs: List[Any]
    reprojection_error: float
    calibration_images: int
    chessboard_size: List[Any]
    image_size: List[int]
    fov: List[int]

    def save_json(self, p: Any):
        results = {
            "camera_matrix": self.camera_matrix.tolist(),
            "dist_coeffs": self.dist_coeffs.tolist(),
            "reprojection_error": self.reprojection_error,
            "calibration_images": self.calibration_images,
            "chessboard_size": self.chessboard_size,
            "fov": self.fov,
            "image_size": self.image_size,
        }
        return json.dump(results, p, indent=2)

    def save_numpy(self, p: Any):
        np.savez(p, camera_matrix=self.camera_matrix, dist_coeffs=self.dist_coeffs)

    def save_text(self, f: Any):
        # 保存为文本格式便于查看
        f.write("相机标定结果\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"棋盘格尺寸: {self.chessboard_size}\n")
        f.write(f"图片尺寸: {self.image_size}\n")
        f.write(f"标定图片数量: {self.calibration_images}\n")
        f.write(f"相机视场角: {self.fov}\n")
        f.write(f"重投影误差: {self.reprojection_error:.6f}\n\n")
        f.write("相机矩阵:\n")
        np.savetxt(f, self.camera_matrix, fmt="%10.5f")
        f.write("\n畸变系数:\n")
        np.savetxt(f, self.dist_coeffs, fmt="%10.5f")


class CameraCalibrator:
    def __init__(self):
        self.chessboard_size = (9, 6, 0.01)  # 默认棋盘格尺寸
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.object_points = []  # 3D世界坐标点
        self.image_points = []  # 2D图像坐标点
        self.image_size = None
        self.calibration_results = None
        self.stop_calibration = False
        self.current_instruction = "请将棋盘格放置在摄像头前"
        self.collected_images = 0

    def set_chessboard_size(self, width: int, height: int, square_size: float):
        """设置棋盘格尺寸"""
        self.chessboard_size = (width, height, square_size)

    def reset(self):
        """重置标定器"""
        self.object_points = []
        self.image_points = []
        self.image_size = None
        self.calibration_results = None
        self.stop_calibration = False
        self.current_instruction = "请将棋盘格放置在摄像头前"
        self.collected_images = 0

    def detect_chessboard(self, frame):
        """检测棋盘格角点"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 调整图像以提高检测效果
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # 尝试检测棋盘格角点
        ret, corners = cv2.findChessboardCorners(
            gray,
            self.chessboard_size[:2],
            cv2.CALIB_CB_ADAPTIVE_THRESH
            + cv2.CALIB_CB_FAST_CHECK
            + cv2.CALIB_CB_NORMALIZE_IMAGE,
        )

        if ret:
            # 精细化角点位置
            corners_refined = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), self.criteria
            )
            return True, corners_refined
        return False, None

    def draw_corners(self, frame):
        """在图像上绘制检测到的角点"""
        ret, corners = self.detect_chessboard(frame)
        if ret:
            cv2.drawChessboardCorners(frame, self.chessboard_size[:2], corners, ret)

            # 添加检测提示
            cv2.putText(
                frame,
                "corner detected!",
                (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
        else:
            cv2.putText(
                frame,
                "no corner",
                (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        return frame

    def get_current_instruction(self):
        """获取当前操作指导"""
        return self.current_instruction

    def auto_calibrate(
        self,
        camera,
        progress_callback: Callable,
        max_images: int = 30,
        min_images: int = 15,
    ):
        """
        自动标定
        Args:
            camera: 摄像头对象
            progress_callback: 进度回调函数
            max_images: 最大采集图片数
            min_images: 最小采集图片数
        """
        self.reset()
        self.stop_calibration = False

        print(f"开始自动标定，棋盘格尺寸: {self.chessboard_size[:2]}")
        print(f"目标采集 {min_images}-{max_images} 张有效图片")

        collected = 0
        last_capture_time = 0
        capture_interval = 1.0  # 采集间隔（秒）

        # 准备3D世界坐标点
        objp = np.zeros(
            (self.chessboard_size[0] * self.chessboard_size[1], 3), np.float32
        )
        objp[:, :2] = np.mgrid[
            0 : self.chessboard_size[0], 0 : self.chessboard_size[1]
        ].T.reshape(-1, 2)
        objp = objp * self.chessboard_size[2]

        while not self.stop_calibration and collected < max_images:
            # 读取摄像头帧
            ret, frame = camera.read()
            if not ret:
                progress_callback(0, "摄像头读取失败")
                time.sleep(0.1)
                continue

            # 保存图像尺寸
            if self.image_size is None:
                self.image_size = (frame.shape[1], frame.shape[0])
                print(f"图像尺寸: {self.image_size}")

            # 检测棋盘格
            ret, corners = self.detect_chessboard(frame)

            current_time = time.time()

            if ret and (current_time - last_capture_time) > capture_interval:
                # 保存角点
                self.object_points.append(objp)
                self.image_points.append(corners)
                collected += 1
                self.collected_images = collected
                last_capture_time = current_time

                # 更新指令
                angle_hint = self._get_angle_hint(collected)
                self.current_instruction = (
                    f"已采集 {collected}/{max_images} 张图片。{angle_hint}"
                )

                # 更新进度
                progress = int((collected / max_images) * 100)
                progress_callback(progress, self.current_instruction)

                print(f"采集第 {collected} 张图片成功")
                time.sleep(0.5)  # 短暂暂停让用户调整位置
            elif ret:
                # 已检测到但时间间隔不够
                remaining_time = capture_interval - (current_time - last_capture_time)
                self.current_instruction = (
                    f"保持姿势... {remaining_time:.1f}秒后采集下一张"
                )
            else:
                # 未检测到棋盘格
                self.current_instruction = "请将棋盘格完整放入视野中，并确保光线充足"

            # 显示进度
            if collected >= min_images:
                self.current_instruction += (
                    f" ({collected}/{max_images})，按停止键可提前完成"
                )

            time.sleep(0.033)  # 约30fps

            # 检查是否达到最小采集数量
            if collected >= min_images and self.stop_calibration:
                break

        # 如果用户提前停止，使用已采集的图片
        final_images = collected
        if final_images < min_images:
            progress_callback(
                0,
                f"采集的图片数量不足，需要至少 {min_images} 张，当前只有 {final_images} 张",
            )
            raise ValueError(
                f"采集的图片数量不足，需要至少 {min_images} 张，当前只有 {final_images} 张"
            )

        print(f"图片采集完成，共采集 {final_images} 张")
        progress_callback(
            100, f"图片采集完成，共 {final_images} 张，正在计算标定参数..."
        )

        # 进行相机标定
        try:
            ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
                self.object_points, self.image_points, self.image_size, None, None
            )

            # 计算重投影误差
            mean_error = 0
            for i in range(len(self.object_points)):
                imgpoints2, _ = cv2.projectPoints(
                    self.object_points[i],
                    rvecs[i],
                    tvecs[i],
                    camera_matrix,
                    dist_coeffs,
                )
                error = cv2.norm(self.image_points[i], imgpoints2, cv2.NORM_L2) / len(
                    imgpoints2
                )
                mean_error += error

            mean_error /= len(self.object_points)

            fov = self._calculate_fov_from_intrinsics(camera_matrix)
            # 保存结果
            self.calibration_results = CalibrationResults(
                camera_matrix=camera_matrix,
                dist_coeffs=dist_coeffs,
                rvecs=rvecs,
                tvecs=tvecs,
                reprojection_error=mean_error,
                calibration_images=final_images,
                chessboard_size=self.chessboard_size,
                image_size=self.image_size,
                fov=fov,
            )

            print(f"标定完成！重投影误差: {mean_error:.6f}")
            print(f"相机视场角: {fov}")
            print(f"相机矩阵:\n{camera_matrix}")
            print(f"畸变系数:\n{dist_coeffs.flatten()}")

            progress_callback(100, f"标定完成！重投影误差: {mean_error:.6f}")

            return self.calibration_results

        except Exception as e:
            progress_callback(0, f"标定计算失败: {str(e)}")
            raise

    def _calculate_fov_from_intrinsics(self, K):
        """
        根据相机内参矩阵计算FOV

        参数:
        K: 3x3相机内参矩阵

        返回:
        fov_horizontal: 水平视场角（度）
        fov_vertical: 垂直视场角（度）
        """
        image_width, image_height = self.image_size
        # 提取内参矩阵参数
        fx = K[0][0]  # x轴焦距
        fy = K[1][1]  # y轴焦距

        # 计算水平FOV
        # fov_h = 2 * arctan(图像宽度 / (2 * fx))
        fov_horizontal_rad = 2 * math.atan(image_width / (2 * fx))
        fov_horizontal_deg = math.degrees(fov_horizontal_rad)

        # 计算垂直FOV
        # fov_v = 2 * arctan(图像高度 / (2 * fy))
        fov_vertical_rad = 2 * math.atan(image_height / (2 * fy))
        fov_vertical_deg = math.degrees(fov_vertical_rad)

        return fov_horizontal_deg, fov_vertical_deg

    def _get_angle_hint(self, image_count: int) -> str:
        """根据采集的图片数量返回角度提示"""
        hints = [
            "正面放置棋盘格",
            "将棋盘格向左倾斜",
            "将棋盘格向右倾斜",
            "将棋盘格向上倾斜",
            "将棋盘格向下倾斜",
            "靠近摄像头",
            "远离摄像头",
            "旋转棋盘格",
            "改变棋盘格角度",
            "尝试不同距离",
        ]

        if image_count <= len(hints):
            return hints[image_count - 1]
        else:
            return f"继续采集不同角度（第{image_count}张）"
