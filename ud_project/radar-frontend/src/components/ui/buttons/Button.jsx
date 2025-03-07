import React from 'react'

function Button(props) {

  return (
   <button className={`button ${props.classNames}`} {...props}>{props.title}</button>
  )
}

export default Button
