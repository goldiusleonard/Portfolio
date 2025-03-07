import React from 'react';

const Sentiment = React.memo(({ data, activeWord }) => {
  const { justification, sentiment } = data || {};

  return (
    <>
      <div className="header-wrapper">
        <div className="active-word">{activeWord}</div>
        <div className="upper-container">
          <span>Sentiment</span>
          <p>{sentiment ?? "N/A"}</p>
        </div>
      </div>
      <div className="desc-wraper">
        <div className="title">Justification</div>
        {justification ? (
          <p className="desc">{justification}</p>
        ) : (
          <div className="no-reply">Justification not supported</div>
        )}
      </div>
    </>
  );
});

const areEqual = (prevProps, nextProps) => {
  return prevProps.activeWord === nextProps.activeWord;
};

export default React.memo(Sentiment, areEqual);

