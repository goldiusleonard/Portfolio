import React from 'react';

const replies = [
    {
        name: "John Doe",
        comment: 'lorem ipsum dolor sit amet consectetur. Magna scelerisque ultrices consectetur quis sit auctor diam. Auctor id aliquam amet fringilla donec ut convallis cursus. Pretium vel sapien pharetra in. Lobortis etiam ac tellus.'
    },
    {
        name: "John Doe",
        comment: 'lorem ipsum dolor sit amet consectetur. Magna scelerisque ultrices consectetur quis sit auctor diam. Auctor id aliquam amet fringilla donec ut convallis cursus. Pretium vel sapien pharetra in. Lobortis etiam ac tellus.'
    },
    {
        name: "John Doe",
        comment: "This is a reply comment"
    }
]

const CommentWithReply = () => {

    return (
        <div className=" d-flex flex-column gap-3 flex-1 ">
            <div className="d-flex justify-content-between align-items-center transition duration-300 background-color: transparent;">
                <span className="font-semibold">Main Comment’s Replies </span>
                <div className="bordered-container">Latest Update: 8/05/2024</div>
            </div>
            <div className='replies-container'>
                {replies.map((reply, index) => (
                    <Reply name={reply.name} comment={reply.comment} key={index} />
                ))}</div>
        </div>
    );
};

export default CommentWithReply;



const Reply = ({ name, comment }) => {
    return (
        <div className="main-comment">
            <div className='image-container bordered-container'>
                <img
                    src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&q=80"
                    alt="Profile"
                    className=" rounded-circle object-cover border-2 border-gray-700 "

                    width='28'
                    height='28'
                />
                {name}
            </div>

            <p className="bordered-container mt-3 p-3 text-justify">
                {comment}
            </p>
        </div>
    )
}