const PDFKeywords = () => {
    const keywords = ['Salary', 'Paycheck', 'Income', 'Earnings', 'Wages', 'Payment', 'Compenation']

    return (
        <div className="pdf-keywords">
            <p>Keyword</p>
            <div className="keyword-content">
                {keywords.map((keyword, idx) => (
                    <div key={idx} className="keyword">{keyword}</div>
                ))}
            </div>
        </div>
    )
}

export default PDFKeywords;