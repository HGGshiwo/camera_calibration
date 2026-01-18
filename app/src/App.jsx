import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import VideoSection from "./components/VideoSection";
import ConfigCard from "./components/ConfigCard";
import StatusCard from "./components/StatusCard";
import ResultsCard from "./components/ResultsCard";
import Instructions from "./components/Instructions";
import {
  getCalibrationStatus,
  startCalibration,
  stopCalibration,
  resetCalibration,
  updateChessboardSize,
  getCalibrationResults,
} from "./utils/api";
import useInterval from "./hooks/setInterval";

function App() {
  const [calibrationState, setCalibrationState] = useState({
    statusText: "等待开始",
    statusColor: "#666",
    progress: 0,
    message: '请设置棋盘格尺寸，然后点击"开始标定"按钮',
    numImages: 0,
    reprojectionError: "-",
    chessboardSize: [9, 6, 0.01],
    isCalibrating: false,
    hasResults: false,
    cameraMatrix: null,
    distCoeffs: null,
    showResultsCard: false,
  });

  const [configState, setConfigState] = useState({
    chessboardWidth: 9,
    chessboardHeight: 6,
    squareSize: 0.01,
    isEditing: false,
    originalWidth: 9,
    originalHeight: 6,
    originalSquareSize: 0.01,
    configMessage: "",
    configMessageType: "",
  });
  const skipNextStatusUpdateRef = useRef(false);

  const updateStatus = async () => {
    if (configState.isEditing || skipNextStatusUpdateRef.current) {
      skipNextStatusUpdateRef.current = false;
      return;
    }

    try {
      const data = await getCalibrationStatus();
      console.log(123, data);
      setCalibrationState((prev) => ({
        ...prev,
        statusText: data.is_calibrating
          ? "标定中..."
          : data.has_results
            ? "标定完成"
            : "等待开始",
        statusColor: data.is_calibrating
          ? "#ff9900"
          : data.has_results
            ? "#4CAF50"
            : "#666",
        progress: data.progress || 0,
        message: data.message || prev.message,
        numImages: data.num_images || 0,
        reprojectionError:
          data.has_results && data.reprojection_error
            ? data.reprojection_error.toFixed(4)
            : "-",
        chessboardSize: data.chessboard_size || prev.chessboardSize,
        isCalibrating: data.is_calibrating || false,
        hasResults: data.has_results || false,
        cameraMatrix: data.camera_matrix || null,
        distCoeffs: data.dist_coeffs || null,
        showResultsCard: data.has_results || false,
      }));

      // 如果不在编辑模式，更新配置中的棋盘格尺寸
      if (!configState.isEditing && data.chessboard_size) {
        setConfigState((prev) => ({
          ...prev,
          chessboardWidth: data.chessboard_size[0],
          chessboardHeight: data.chessboard_size[1],
          squareSize: data.chessboard_size[2],
        }));
      }
    } catch (error) {
      console.error("获取标定状态失败:", error);
    }
  };

  const clear = useInterval(() => {
    if (!configState.isEditing) {
      updateStatus();
    }
  }, 1000);

  useEffect(() => {
    // 初始状态更新
    updateStatus();

    // 启动状态轮询

    // 清理函数
    return () => {
      clear();
    };
  }, []);

  const handleStartCalibration = async () => {
    const { chessboardWidth, chessboardHeight, squareSize } = configState;

    // 验证输入
    if (chessboardWidth < 3 || chessboardHeight < 3) {
      alert("棋盘格尺寸至少为3x3");
      return;
    }

    if (chessboardWidth > 15 || chessboardHeight > 15) {
      alert("棋盘格尺寸最大为15x15");
      return;
    }

    try {
      const data = await startCalibration(
        chessboardWidth,
        chessboardHeight,
        squareSize,
      );
      if (data.status === "success") {
        alert(
          `标定已开始，棋盘格尺寸: ${chessboardWidth}x${chessboardHeight}\n请按照屏幕提示移动棋盘格`,
        );
        // 重新启动状态轮询
        updateStatus();
      } else {
        alert("错误: " + data.message);
      }
    } catch (error) {
      alert("无法连接到服务器");
    }
  };

  const handleStopCalibration = async () => {
    try {
      const data = await stopCalibration();
      if (data.status === "success") {
        alert("标定已停止");
        updateStatus();
      }
    } catch (error) {
      alert("无法连接到服务器");
    }
  };

  const handleResetCalibration = async () => {
    if (window.confirm("确定要重置标定吗？所有标定数据将丢失。")) {
      try {
        const data = await resetCalibration();
        if (data.status === "success") {
          alert("标定已重置");
          updateStatus();
        }
      } catch (error) {
        alert("无法连接到服务器");
      }
    }
  };

  const handleEditMode = () => {
    if (configState.isEditing) return;

    setConfigState((prev) => ({
      ...prev,
      isEditing: true,
      originalWidth: prev.chessboardWidth,
      originalHeight: prev.chessboardHeight,
      squareSize: prev.squareSize,
      configMessage: "",
      configMessageType: "",
    }));
  };

  const handleCancelEdit = () => {
    if (!configState.isEditing) return;

    setConfigState((prev) => ({
      ...prev,
      isEditing: false,
      chessboardWidth: prev.originalWidth,
      chessboardHeight: prev.originalHeight,
      squareSize: prev.squareSize,
      configMessage: "",
      configMessageType: "",
    }));
  };

  const handleConfirmEdit = async () => {
    const { chessboardWidth, chessboardHeight, squareSize } = configState;

    // 验证输入
    if (chessboardWidth < 3 || chessboardHeight < 3) {
      setConfigState((prev) => ({
        ...prev,
        configMessage: "棋盘格尺寸至少为3x3",
        configMessageType: "error",
      }));
      return;
    }

    if (chessboardWidth > 15 || chessboardHeight > 15) {
      setConfigState((prev) => ({
        ...prev,
        configMessage: "棋盘格尺寸最大为15x15",
        configMessageType: "error",
      }));
      return;
    }

    try {
      const data = await updateChessboardSize(
        chessboardWidth,
        chessboardHeight,
        squareSize,
      );
      if (data.status === "success") {
        setConfigState((prev) => ({
          ...prev,
          configMessage: data.message,
          configMessageType: "success",
        }));

        // 设置跳过下一次状态更新
        skipNextStatusUpdateRef.current = true;

        // 延迟一小段时间再更新状态
        setTimeout(() => {
          updateStatus();
          // 退出编辑模式
          setConfigState((prev) => ({
            ...prev,
            isEditing: false,
            configMessage: "",
            configMessageType: "",
          }));
        }, 100);
      } else {
        setConfigState((prev) => ({
          ...prev,
          configMessage: "错误: " + data.message,
          configMessageType: "error",
        }));
      }
    } catch (error) {
      setConfigState((prev) => ({
        ...prev,
        configMessage: "无法连接到服务器",
        configMessageType: "error",
      }));
    }
  };

  const handleDownloadResults = async () => {
    try {
      const data = await getCalibrationResults();
      if (data.status === "success") {
        // 创建下载链接
        const dataStr = JSON.stringify(data.results, null, 2);
        const dataBlob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(dataBlob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "camera_calibration_results.json";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        alert("未找到标定结果");
      }
    } catch (error) {
      alert("下载失败");
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    const parseFunc = name == "squareSize" ? parseFloat : parseInt;
    setConfigState((prev) => ({
      ...prev,
      [name]: parseFunc(value) || "",
    }));
  };

  const handleInputBlur = (fieldName) => {
    const {
      isEditing,
      originalWidth,
      originalHeight,
      originalSquareSize,
      chessboardWidth,
      chessboardHeight,
      squareSize,
    } = configState;

    if (isEditing) {
      if (
        (fieldName === "width" && chessboardWidth !== originalWidth) ||
        (fieldName === "height" && chessboardHeight !== originalHeight) ||
        (fieldName == "square_size" && squareSize !== originalSquareSize)
      ) {
        setConfigState((prev) => ({
          ...prev,
          configMessage: '尺寸已修改，请点击"确认修改"按钮保存',
          configMessageType: "success",
        }));
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && configState.isEditing) {
      handleConfirmEdit();
    }
  };

  return (
    <div className="container">
      <header>
        <h1>📷 摄像头自动标定系统</h1>
        <p className="subtitle">自动从视频流中检测棋盘格并完成相机标定</p>
      </header>

      <div className="main-content">
        <div>
          <VideoSection
            onStart={handleStartCalibration}
            onStop={handleStopCalibration}
            onReset={handleResetCalibration}
            isCalibrating={calibrationState.isCalibrating}
            hasResults={calibrationState.hasResults}
          />
          <Instructions />
        </div>
        <div className="control-section">
          <ConfigCard
            configState={configState}
            onEdit={handleEditMode}
            onCancel={handleCancelEdit}
            onConfirm={handleConfirmEdit}
            onInputChange={handleInputChange}
            onInputBlur={handleInputBlur}
            onKeyPress={handleKeyPress}
          />
          
          <StatusCard
            statusText={calibrationState.statusText}
            statusColor={calibrationState.statusColor}
            progress={calibrationState.progress}
            instructionText={calibrationState.message}
            collectedImages={calibrationState.numImages}
            reprojectionError={calibrationState.reprojectionError}
            currentSize={`${calibrationState.chessboardSize[0]}x${calibrationState.chessboardSize[1]}`}
          />

          {calibrationState.showResultsCard && (
            <ResultsCard
              cameraMatrix={calibrationState.cameraMatrix}
              distCoeffs={calibrationState.distCoeffs}
              chessboardSize={calibrationState.chessboardSize}
              onDownload={handleDownloadResults}
            />
          )}
        </div>
      </div>

      <footer>
        <p>摄像头自动标定系统 &copy; 2023</p>
      </footer>
    </div>
  );
}

export default App;
