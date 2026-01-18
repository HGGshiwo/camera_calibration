import React from 'react';

const Instructions = () => {
  return (
    <div className="instructions">
      <h3>使用说明</h3>
      <ol>
        <li>点击"编辑尺寸"按钮修改棋盘格内角点尺寸（宽度和高度）</li>
        <li>点击"确认修改"按钮保存尺寸，系统将自动重置标定状态</li>
        <li>准备对应尺寸的棋盘格（例如：9x6表示棋盘格有9列6行内角点）</li>
        <li>点击"开始标定"按钮</li>
        <li>按照屏幕提示移动棋盘格到不同位置和角度</li>
        <li>系统会自动采集足够多样本后计算标定参数</li>
        <li>完成后可以下载标定结果</li>
      </ol>
      <p className="note">
        注意: 确保棋盘格完全可见，光照均匀，避免反光。内角点是指棋盘格内部黑白方格相交的点。
      </p>
    </div>
  );
};

export default Instructions;