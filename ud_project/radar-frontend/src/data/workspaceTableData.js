import { CustomBox, CustomRiskBox, WSCustomBox} from "../components/tables/CustomBox";
import {AvatarWithText} from "../components/tables/AvatarWithText";
import {Ahmed,Azman, Farida, Kamal, Hafiz, Kim, Saleh, Sameer,Siti } from '../assets/images'

export const dummyWorkspaceTableData = [
	{
		video_id: "123456",
		video_posted_timestamp: "2021-05-07 09:00:00",
		video_source: "Facebook",
		sub_category: "Fake News",
		status: "Flagged",
		risk_status: "High",
	},
	{
		video_id: "123457",
		video_posted_timestamp: "2021-05-07 09:00:00",
		video_source: "Facebook",
		sub_category: "Fake News",
		status: "Flagged",
		risk_status: "High",
	},
	{
		video_id: "123458",
		video_posted_timestamp: "2021-05-07 09:00:00",
		video_source: "Facebook",
		sub_category: "Fake News",
		status: "Flagged",
		risk_status: "High",
	},
	{
		video_id: "123459",
		video_posted_timestamp: "2021-05-07 09:00:00",
		video_source: "Facebook",
		sub_category: "Fake News",
		status: "Flagged",
		risk_status: "High",
	},
	{
		video_id: "123460",
		video_posted_timestamp: "2021-05-07 09:00:00",
		video_source: "Facebook",
		sub_category: "Fake News",
		status: "Flagged",
		risk_status: "High",
	},
	{
		video_id: "123461",
		video_posted_timestamp: "2021-05-07 09:00:00",
		video_source: "Facebook",
		sub_category: "Fake News",
		status: "Flagged",
		risk_status: "High",
	},
	{
		video_id: "123462",
		video_posted_timestamp: "2021-05-07 09:00:00",
		video_source: "Facebook",
		sub_category: "Fake News",
		status: "Flagged",
		risk_status: "High",
	},
	{
		video_id: "123463",
		video_posted_timestamp: "2021-05-07 09:00:00",
		video_source: "Facebook",
		sub_category: "Fake News",
		status: "Flagged",
		risk_status: "High",
	},

];

// dont delete this;
const DateAndTime = ({ content_date }) => {
	// 2024-04-19T11:29:02
	let date = new Date(content_date);
	let dateStr = date.toLocaleDateString();
	let timeStr = date.toLocaleTimeString();
	dateStr = dateStr + " " + timeStr;
	return <div>{dateStr}</div>;
}

const CustomDateAndTime = ({ video_posted_timestamp }) => {
	// 2024-04-19T11:29:02
	let date = new Date(video_posted_timestamp);
	let dateStr = date.toLocaleDateString();
	let timeStr = date.toLocaleTimeString();
	dateStr = dateStr + " " + timeStr;
	return <div>{dateStr}</div>;
}
export const contentsListHeaders = [
	{ field: "identification_id", header: "Content ID" },
	{ field: "content_date", header: "Date and Time", body: DateAndTime },
	{ field: "social_media_type", header: "Social Media" },
	{ field: "sub_category", header: "Sub-Category", style: { textTransform: 'Capitalize' } },
	// { field: "status", header: "Status of Content" },
	{ field: "risk_level", header: "Risk", body: CustomRiskBox },
];

export const similarContentsListHeaders = [
	{ field: "identification_id", header: "Content ID" },
	{ field: "video_posted_timestamp", header: "Date and Time", body: CustomDateAndTime },
	{ field: "video_source", header: "Social Media" },
	{ field: "sub_category", header: "Sub-Category", style: { textTransform: 'Capitalize' } },
	// { field: "status", header: "Status of Content" },
	{ field: "risk_status", header: "Risk", body: CustomBox },
];


const similarContentList = [
	{
		"video_id": 22,
		"identification_id": "TK240601SFH000022",
		"video_posted_timestamp": "2024-04-04T08:34:51",
		"video_source": "TikTok",
		"ai_topic": "Forex Education",
		"status": "AI Flagged",
		"risk_status": "high",
		"sub_category": "forex",
		"user_handle": "finihazlitc",
		"video_api_id": "7353803842087177489",
		"video_url": "https://blobstrgmcmc.blob.core.windows.net/videofiles/7353803842087177489.mp4?se=2027-01-31T10%3A16%3A42Z&sp=r&sv=2023-11-03&sr=b&sig=qU2C27hrc0xNmefH3iy2cBSWM504HJr/qTplQ58y6RI%3D",
		"video_screenshot_url": "https://blobstrgmcmc.blob.core.windows.net/screenshotfile/7353803842087177489.png?se=2027-01-31T10%3A16%3A43Z&sp=r&sv=2023-11-03&sr=b&sig=hQw9sx8hjRDF9gDhk9qwb/aVuHhnJw7HMg6IgdiQECU%3D",
		"video_justification": "This video is a scam. The speaker claims that the investment group is a legitimate entity, but fails to provide any evidence to support this claim. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users."
	},
	{
		"video_id": 24,
		"identification_id": "TK240601SFL000024",
		"video_posted_timestamp": "2024-03-31T22:16:50",
		"video_source": "TikTok",
		"ai_topic": "Forex Education",
		"status": "AI Flagged",
		"risk_status": "low",
		"sub_category": "forex",
		"user_handle": "finihazlitc",
		"video_api_id": "7352531330468449553",
		"video_url": "https://blobstrgmcmc.blob.core.windows.net/videofiles/7352531330468449553.mp4?se=2027-01-31T10%3A17%3A06Z&sp=r&sv=2023-11-03&sr=b&sig=VkaM7ShbOOXYwZIu8JaE3cnKfO/MdIYFwYSCE9UaRNI%3D",
		"video_screenshot_url": "https://blobstrgmcmc.blob.core.windows.net/screenshotfile/7352531330468449553.png?se=2027-01-31T10%3A17%3A07Z&sp=r&sv=2023-11-03&sr=b&sig=QzrBbjCwBll7SL8OEN18frS69quig8ji%2BE0NBrH%2B3t0%3D",
		"video_justification": "This video is a scam. The speaker claims that the investment group is a legitimate entity, but fails to provide any evidence to support this claim. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users."
	},
	{
		"video_id": 94,
		"identification_id": "TK240601SFH000094",
		"video_posted_timestamp": "2024-01-13T16:15:23",
		"video_source": "TikTok",
		"ai_topic": "Forex Profit",
		"status": "AI Flagged",
		"risk_status": "high",
		"sub_category": "forex",
		"user_handle": "finihazlitc",
		"video_api_id": "7323493525167934722",
		"video_url": "https://blobstrgmcmc.blob.core.windows.net/videofiles/7323493525167934722.mp4?se=2027-01-31T10%3A37%3A06Z&sp=r&sv=2023-11-03&sr=b&sig=iJ275yoic0f8H2EuE7P0eLVQXzshGdoUItwc/iZneZA%3D",
		"video_screenshot_url": "https://blobstrgmcmc.blob.core.windows.net/screenshotfile/7323493525167934722.png?se=2027-01-31T10%3A37%3A07Z&sp=r&sv=2023-11-03&sr=b&sig=rpLBvtdC3CKx/fSA2WkrsvJv8mQItDndZeX615sCe9g%3D",
		"video_justification": "This video is a scam. The speaker claims that the investment group is a legitimate entity, but fails to provide any evidence to support this claim. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users. The speaker also fails to provide any information on the investment process, focusing solely on potential profits for users."
	},
]

export const activityTableData = [
	{
		date: '13 July',
		time: '1:32 pm',
		user_handle: 'Ahmad Faiz',
		officerTitle: 'Officer',
		event: 'Creat Pipeline for Bitcoin',
		profile_picture_link: Ahmed
	},
	{
		date: '13 July',
		time: '12:30 pm',
		user_handle: 'Farida Aminah',
		officerTitle: 'Officer',
		event: 'Reported FB240228CBMM000015',
		profile_picture_link: Farida
	},
	{
		date: '13 July',
		time: '11:14 am',
		user_handle: 'Hafiz Rahman',
		officerTitle: 'Officer',
		event: 'Reported FB240228CBMM000016',
		profile_picture_link: Hafiz
	},
	{
		date: '13 July',
		time: '11:06 am',
		user_handle: 'Kamal Adnan',
		officerTitle: 'Manager',
		event: 'Assign new task to Farida Aminah',
		profile_picture_link: Kamal
	},
	{
		date: '13 July',
		time: '11:00 am',
		user_handle: 'Siti Aishah',
		officerTitle: 'Officer',
		event: 'Reported FB240228CBMM000019',
		profile_picture_link: Siti
	},
	{
		date: '13 July',
		time: '10:53 am',
		user_handle: 'Azman Idris',
		officerTitle: 'Officer',
		event: 'Reported TK240228CBMM000022',
		profile_picture_link: Azman
	},
	{
		date: '13 July',
		time: '1:32 pm',
		user_handle: 'Sameer Anand',
		officerTitle: 'Officer',
		event: 'Reported TK240228CBMM000027',
		profile_picture_link: Sameer
	},
	{
		date: '13 July',
		time: '1:32 pm',
		user_handle: 'Kim Lau Ng',
		officerTitle: 'Officer',
		event: 'Reported FB240228CBMM000029',
		profile_picture_link: Kim
	},


];

export const activityTabHeaders = [

	{ field: "date", header: "Date & Time", body: DateUi  },
	{ field: "user_handle", header: "Name", body:AvatarWithText },
	{ field: "officerTitle", header: "Title", body: Title },
	{ field: "event", header: "Event" },
]

function Title(rowData) {

	const bgColor= rowData.officerTitle.toLowerCase()==='officer'? '#A87972':'#728EA8'

	return <button className="activity-title " style={{backgroundColor:bgColor}} >
		{rowData.officerTitle}
	</button>
}

function DateUi (rowData){

	return <div className='activity-date'>  
		<p>
			{rowData.date}
		</p>
		<p className="activity-time">
		{rowData.time}
		</p>

	</div>
}

// note :this class in workspacce