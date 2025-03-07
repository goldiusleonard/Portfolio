const PDFHashtags = () => {
    const hashtags = [
        {
            label: '#learnontiktok',
            risk: 'High',
        },
        {
            label: '#foryou',
            risk: 'High',
        },
        {
            label: '#streetinterview',
            risk: 'High',
        },
        {
            label: '#salary',
            risk: 'High',
        },
        {
            label: '#career',
            risk: 'High',
        },
        {
            label: '#urban',
            risk: 'High',
        },
        {
            label: '#living',
            risk: 'High',
        },
        {
            label: '#kualalumpur',
            risk: 'High',
        },
        {
            label: '#malaysia',
            risk: 'High',
        },
        {
            label: '#fyp',
            risk: 'High',
        },
        {
            label: '#viral',
            risk: 'High',
        },
    ]

    return (
        <div className="pdf-hashtags">
            <p>Hashtags</p>
            <div className="hashtags-content">
                {hashtags.map((hashtag, idx) => (
                    <div key={idx} className="hashtag">
                        <p>{hashtag.label}</p>
                        <div className="risk">{hashtag.risk}</div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default PDFHashtags;