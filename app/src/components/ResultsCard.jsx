
const ResultsCard = ({ cameraMatrix, distCoeffs, chessboardSize, fov, onDownload }) => {
  return (
    <div className="results-card">
      <h2>标定结果</h2>
      <div className="results-content">
        <div className="result-item">
          <div className="result-label">相机矩阵:</div>
          <pre id="camera-matrix" className="result-value">
            {cameraMatrix ? JSON.stringify(cameraMatrix, null, 2) : '未计算'}
          </pre>
        </div>
        <div className="result-item">
          <div className="result-label">畸变系数:</div>
          <pre id="dist-coeffs" className="result-value">
            {distCoeffs ? JSON.stringify(distCoeffs, null, 2) : '未计算'}
          </pre>
        </div>
        <div className="result-item">
          <div className="result-label">相机视场角:</div>
          <pre id="fov" className="result-value">
            {fov ? JSON.stringify(fov, null, 2) : '未计算'}
          </pre>
        </div>
        <div className="result-item">
          <div className="result-label">棋盘格尺寸:</div>
          <pre id="chessboard-size-result" className="result-value">
            {chessboardSize ? JSON.stringify(chessboardSize, null, 2) : '未计算'}
          </pre>
        </div>
        <button id="download-btn" className="btn btn-success" onClick={onDownload}>
          下载标定结果
        </button>
      </div>
    </div>
  );
};

export default ResultsCard;