const PDFTopComments = () => {
    const topComments = [
        {
            title: 'xavier090822',
            description: '4000-5000 = comfortable 7000 = very comfortable 10000 dah T20. for single.',
            rate: '1-20'
        },
        {
            title: 'xavier090822',
            description: '4000-5000 = comfortable 7000 = very comfortable 10000 dah T20. for single.',
            rate: '1-20'
        },
        {
            title: 'xavier090822',
            description: '4000-5000 = comfortable 7000 = very comfortable 10000 dah T20. for single.',
            rate: '1-18'
        },
        {
            title: 'xavier090822',
            description: '4000-5000 = comfortable 7000 = very comfortable 10000 dah T20. for single.',
            rate: '1-10'
        },
        {
            title: 'xavier090822',
            description: '4000-5000 = comfortable 7000 = very comfortable 10000 dah T20. for single.',
            rate: '1-15'
        },
        {
            title: 'xavier090822',
            description: '4000-5000 = comfortable 7000 = very comfortable 10000 dah T20. for single.',
            rate: '1-20'
        },
        {
            title: 'xavier090822',
            description: '4000-5000 = comfortable 7000 = very comfortable 10000 dah T20. for single.',
            rate: '1-20'
        },
    ]
    
    return (
        <div className="pdf-top-comments">
            <div className="pdf-top-comments-header">
                <p>Top Comments</p>
                <div className="last-update">Lastest Update: 2022-01-01</div>
            </div>
            {topComments.map((item, index) => {
                return (
                    <div className=" pdf-top-comments-card">
                        <div className="right">
                            <img src="https://cdn-icons-png.flaticon.com/512/10337/10337609.png" alt="Profile"/>
                            <div className="text">
                                <p>{item.title}</p>
                                <p>{item.description}</p>
                            </div>
                        </div>
                        <div className="left">
                            <p>1{item.rate}</p>
                        </div>
                    </div>
                )
            })}
           
        </div>
    )
}

export default PDFTopComments;