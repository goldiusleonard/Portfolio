import React from 'react'

//Props
// {
//   data: [] of string
// }

const TagList = ({
  data = []
}) => {
  const isDataMoreThanThree = data.length > 3
  const tags = isDataMoreThanThree ? data.slice(0, 3) : data

  const Tag = ({ value }) => {
    return (
      <div className="tag">
        {value}
      </div>
    )
  }

  const HoverTag = ({
    data
  }) => {
    return (
      <div className="hover-tag">
        <div className="trigger">
          <Tag value={'4+'} />
        </div>

        <div className="content">
          {data.map((v, idx) =>
            <span key={idx}>
              {v}
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="tag-list">
      {tags.map((v, idx) =>
        <Tag
          key={idx}
          value={v} />
      )}
      {isDataMoreThanThree && <HoverTag data={data.slice(3)} />}
    </div>
  )
}

export default TagList