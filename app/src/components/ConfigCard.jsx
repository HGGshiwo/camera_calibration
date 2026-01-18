import React from "react";

const ConfigCard = ({
  configState,
  onEdit,
  onCancel,
  onConfirm,
  onInputChange,
  onInputBlur,
  onKeyPress,
}) => {
  const {
    chessboardWidth,
    chessboardHeight,
    squareSize,
    isEditing,
    configMessage,
    configMessageType,
  } = configState;

  return (
    <div className="config-card">
      <h2>标定配置</h2>
      <div className="config-form">
        <div className="form-group">
          <label htmlFor="chessboard-width">棋盘格宽度 (内角点数):</label>
          <input
            type="number"
            id="chessboard-width"
            name="chessboardWidth"
            className="form-control"
            min="3"
            max="15"
            value={chessboardWidth}
            readOnly={!isEditing}
            onChange={onInputChange}
            onBlur={() => onInputBlur("width")}
            onKeyPress={onKeyPress}
          />
        </div>
        <div className="form-group">
          <label htmlFor="chessboard-height">棋盘格高度 (内角点数):</label>
          <input
            type="number"
            id="chessboard-height"
            name="chessboardHeight"
            className="form-control"
            min="3"
            max="15"
            value={chessboardHeight}
            readOnly={!isEditing}
            onChange={onInputChange}
            onBlur={() => onInputBlur("height")}
            onKeyPress={onKeyPress}
          />
        </div>
        <div className="form-group">
          <label htmlFor="square-size">棋盘格物理长度(m):</label>
          <input
            type="number"
            id="square-size"
            name="squareSize"
            className="form-control"
            min="0"
            max="0.5"
            value={squareSize}
            readOnly={!isEditing}
            onChange={onInputChange}
            onBlur={() => onInputBlur("square_size")}
            onKeyPress={onKeyPress}
          />
        </div>
        <div className="form-buttons">
          {!isEditing && (
            <button id="edit-btn" className="btn btn-edit" onClick={onEdit}>
              编辑尺寸
            </button>
          )}
          {isEditing && (
            <>
              <button
                id="confirm-btn"
                className="btn btn-confirm"
                onClick={onConfirm}
              >
                确认修改
              </button>
              <button
                id="cancel-btn"
                className="btn btn-cancel"
                onClick={onCancel}
              >
                取消
              </button>
            </>
          )}
        </div>
        {configMessage && (
          <div
            id="config-message"
            className={`config-message ${configMessageType}`}
          >
            {configMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConfigCard;
