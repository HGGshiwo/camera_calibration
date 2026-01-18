const API_BASE = process.env.NODE_ENV === 'development' ? 'http://localhost:5000': ''; // 根据实际后端地址设置

export const getVideoFeed = () => `${API_BASE}/video_feed`

export const getCalibrationStatus = async () => {
  try {
    const response = await fetch(`${API_BASE}/get_calibration_status`);
    if (!response.ok) {
      throw new Error('获取状态失败');
    }
    return await response.json();
  } catch (error) {
    console.error('获取标定状态失败:', error);
    throw error;
  }
};

export const startCalibration = async (chessboardWidth, chessboardHeight, squareSize) => {
  try {
    const response = await fetch(`${API_BASE}/start_calibration`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chessboard_width: chessboardWidth,
        chessboard_height: chessboardHeight,
        square_size: squareSize,
      }),
    });
    if (!response.ok) {
      throw new Error('启动标定失败');
    }
    return await response.json();
  } catch (error) {
    console.error('启动标定失败:', error);
    throw error;
  }
};

export const stopCalibration = async () => {
  try {
    const response = await fetch(`${API_BASE}/stop_calibration`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error('停止标定失败');
    }
    return await response.json();
  } catch (error) {
    console.error('停止标定失败:', error);
    throw error;
  }
};

export const resetCalibration = async () => {
  try {
    const response = await fetch(`${API_BASE}/reset_calibration`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error('重置标定失败');
    }
    return await response.json();
  } catch (error) {
    console.error('重置标定失败:', error);
    throw error;
  }
};

export const updateChessboardSize = async (chessboardWidth, chessboardHeight, squareSize) => {
  try {
    const response = await fetch(`${API_BASE}/update_chessboard_size`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chessboard_width: chessboardWidth,
        chessboard_height: chessboardHeight,
        square_size: squareSize 
      }),
    });
    if (!response.ok) {
      throw new Error('更新尺寸失败');
    }
    return await response.json();
  } catch (error) {
    console.error('更新尺寸失败:', error);
    throw error;
  }
};

export const getCalibrationResults = async () => {
  try {
    const response = await fetch(`${API_BASE}/get_calibration_results`);
    if (!response.ok) {
      throw new Error('获取结果失败');
    }
    return await response.json();
  } catch (error) {
    console.error('获取标定结果失败:', error);
    throw error;
  }
};