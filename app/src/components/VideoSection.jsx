import React from 'react';
import { getVideoFeed } from '../utils/api';

const VideoSection = ({ onStart, onStop, onReset, isCalibrating, hasResults }) => {
  return (
    <div className="video-section">
      <div className="video-container">
        <h2>实时视频流</h2>
        <div className="video-wrapper">
          <img
            src={getVideoFeed()} // 根据实际后端API调整
            id="video-feed"
            alt="摄像头视频流"
          />
        </div>
        <div className="video-controls">
          <button 
            id="start-btn" 
            className="btn btn-primary"
            onClick={onStart}
            disabled={isCalibrating}
          >
            开始标定
          </button>
          <button 
            id="stop-btn" 
            className="btn btn-secondary" 
            onClick={onStop}
            disabled={!isCalibrating}
          >
            停止标定
          </button>
          <button 
            id="reset-btn" 
            className="btn btn-warning"
            onClick={onReset}
          >
            重置标定
          </button>
        </div>
      </div>
    </div>
  );
};

export default VideoSection;