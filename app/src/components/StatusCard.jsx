import React from 'react';

const StatusCard = ({
  statusText,
  statusColor,
  progress,
  instructionText,
  collectedImages,
  reprojectionError,
  currentSize
}) => {
  return (
    <div className="status-card">
      <h2>标定状态</h2>
      <div className="status-indicator">
        <div className="status-label">状态:</div>
        <div id="status-text" className="status-value" style={{ color: statusColor }}>
          {statusText}
        </div>
      </div>

      <div className="progress-container">
        <div className="progress-label">
          <span>进度:</span>
          <span id="progress-text">{progress}%</span>
        </div>
        <div className="progress-bar">
          <div 
            id="progress-fill" 
            className="progress-fill"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      <div className="instruction-box">
        <h3>用户指导</h3>
        <div id="instruction-text" className="instruction-text">
          {instructionText}
        </div>
      </div>

      <div className="stats-box">
        <h3>标定统计</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <div className="stat-label">已采集图片</div>
            <div id="collected-images" className="stat-value">{collectedImages}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">重投影误差</div>
            <div id="reprojection-error" className="stat-value">{reprojectionError}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">棋盘格尺寸</div>
            <div id="current-size" className="stat-value">{currentSize}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusCard;