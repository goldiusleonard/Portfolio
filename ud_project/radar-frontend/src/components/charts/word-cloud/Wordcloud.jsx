import React from 'react';


export const Wordcloud =React.memo (({ words, onWordClick }) => {

    const data=words?.slice(0,20)


   const sum = data?.reduce((acc, curr) => acc + curr.value, 0);
   const average = sum / data?.length;

    return (

        <div className='inner-container'>
            {data?.map((word, index) => (
                <Text key={index} word={word.word}   isSmallClass ={ word?.value < average ? 'word-small' : 'word'}/>
            ))}
        </div>

    );
})

const Text = ({ word, isSmallClass  }) => {
   
    return (
        <span className={isSmallClass}>
            {word}
        </span>
    );
};


