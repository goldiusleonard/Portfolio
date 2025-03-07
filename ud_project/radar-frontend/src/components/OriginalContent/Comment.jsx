import React from "react";
import "./Comment.scss";
import { PromptSuggestionIcon, ThumbUpIcon } from "../../assets/icons";
import formatNumber from "../../Util/NumberFormat";

const Comment = ({ img_url, comment, name, shares, likes }) => {
	return (
		<div className="comment-container">
			<div className="user-info">
				{/* <img
					src={img_url}
					alt="User Avatar"
					className="avatar"
				/> */}
				<span className="username">{name}</span>
			</div>
			<div className="comment-content">
				<p>
					{comment}
				</p>
			</div>
			{/* <div className="comment-actions">
				<PromptSuggestionIcon fill={"#A9A9A9"} />
				<span className="reply">
					{formatNumber(shares)}
				</span>
				<ThumbUpIcon fill={"#A9A9A9"} />
				<span className="like">
					{formatNumber(likes)}
				</span>
			</div> */}
		</div>
	);
};

export default Comment;
