import React, { useEffect, useState } from 'react'
import penIcon from '../../assets/icons/pen.svg'
import binIcon from '../../assets/icons/bin.svg'

const KeywordList = ({
  keywords = [],
  usernames = [],
  onChangeKeywords,
  onChangeUsernames,
 isUsernameCrawler,
 isKeywordCrawler,
 setEditedAgentData
  
}) => {
  let categories = []


if (isUsernameCrawler && !isKeywordCrawler) {
  categories = ['Username']
}
if (isKeywordCrawler && !isUsernameCrawler) {
  categories = ['Keyword']
}
if (isKeywordCrawler && isUsernameCrawler) {
  categories = ['Keyword', 'Username']
  
}

  const [selectedCategory, setSelectionCategory] = useState(categories[0])
  const [keyword, setKeyword] = useState('')
  const [dataByCategory, setDataByCategory] = useState(keywords)

  const [editIndex, setEditIndex] = useState(null);
  const [editValue, setEditValue] = useState('');


  useEffect(() => {
    onChangeDataByCategory(selectedCategory === 'Keyword' ? keywords : usernames)
  }, [selectedCategory, keywords, usernames])

  const onChangeDataByCategory = (data) => {
    setDataByCategory(data)
  }

  const handleSelectCategory = (value) => {
    setSelectionCategory(value)
    setEditIndex(null);
  }

  const onChangeKeyword = (e) => {
    setKeyword(e.target.value)
  }

  
  const onAddKeyword = () => {
    const newData = selectedCategory === 'Keyword' ? [...keywords, keyword] : [...usernames, keyword];
    if (selectedCategory === 'Keyword' && onChangeKeywords) {
      setEditedAgentData((prev) => ({ ...prev, keywordList: [...newData] }));
      onChangeKeywords(newData)
    } else if (onChangeUsernames) {
      onChangeUsernames(newData)
      setEditedAgentData((prev) => ({ ...prev, usernameList: [...newData] }));
    }
    setKeyword('')
  }
  

  const onRemove = (idx) => {
    const newData = dataByCategory.filter((_, i) => i !== idx);

    if (selectedCategory === 'Keyword' && onChangeKeywords) {
      onChangeKeywords(newData);
    } else if (onChangeUsernames) {
      onChangeUsernames(newData);
    }
     setEditIndex(null)
  }

  const handleEdit = (idx, value) => {
    setEditIndex(idx);
    setEditValue(value);
  };

  const handleSaveEdit = (idx) => {
    const newData = [...dataByCategory];
    newData[idx] = editValue;

    if (selectedCategory === 'Keyword' && onChangeKeywords) {
      onChangeKeywords(newData);
    } else if (onChangeUsernames) {
      onChangeUsernames(newData);
    }

    setEditIndex(null);
    setEditValue('');
  };

  const handleEditInputChange = (e) => {
    setEditValue(e.target.value);
  };


  return (
    <div className="keyword-list">
      <div className="tab-btn">
        {categories.map((v, idx) =>
          <button
            key={idx}
            className={v === selectedCategory ? 'active' : ''}
            onClick={() => handleSelectCategory(v)}
          >
            {v}
          </button>
        )}
      </div>

      {dataByCategory.length === 0 &&
        <div className="empty-list">
          no keywords/usernames yet
        </div>
      }

      {dataByCategory.length > 0 &&
        <div className="list-container">
          {
            dataByCategory.map((v, idx) =>
              <div
                key={idx}
                className="item"
              >
                {editIndex === idx ? (
                  <div className="edit-input">
                    <input type="text" value={editValue} onChange={handleEditInputChange} />
                  </div>
                ) : (
                  <span>{v}</span>
                )}
                <div className="btn-container">
                  {editIndex === idx ? <>
                    <button onClick={() => handleSaveEdit(idx)}>Save</button>
                    <button onClick={() => setEditIndex(null)}>Cancel</button>
                  </> : <>
                  <button onClick={() => handleEdit(idx, v)}>
                    <img
                      src={penIcon}
                      alt='edit icon'
                      width={20} />
                  </button>
                  <button onClick={() => onRemove(idx)}>
                    <img
                      src={binIcon}
                      alt='delete icon'
                      width={20} />
                  </button>
                  </>
                 }
                  
                </div>
              </div>
            )
          }
        </div>
      }

      <form onSubmit={e => e.preventDefault()}>
        <input
          placeholder="Type New Keyword"
          value={keyword}
          onChange={onChangeKeyword}
        />

        <button
          className='btn'
          onClick={onAddKeyword}
          disabled={!keyword}
        >
          Add Keyword
        </button>
      </form>
    </div>
  )
}

export default KeywordList