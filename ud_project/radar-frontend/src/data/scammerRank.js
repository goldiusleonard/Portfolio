import moment from "moment";
import {AvatarWithText} from "../components/tables/AvatarWithText";
import  { CustomBox } from '../components/tables/CustomBox'
import formatDate from "../components/tables/DateFormatter";
import { formatRowDate } from "../Util/DateFormat";


const threatLevelformat = (rowData) => {
    // const roundedValue = Math.round(rowData.ProfileThreatLevel);

    const rounded = Math.round(rowData * 10) / 10;
    const roundedValue =  rounded % 1 === 0 ? rounded.toFixed(0) : rounded.toFixed(1);
    return (<div className="threat-level" style={{color:'#ffffff', fontSize:'16px'}}>{roundedValue}%</div>);
};

const TextWithHash = (rowData) => {
    return (
        <div className="text-capitalized">#{rowData.rank_engagement}</div>
    );
};



export const scammersRankingHeaders = [
    { field: 'user_handle', header: 'Name', body: AvatarWithText },
    { field: 'ProfileEngagement_score', header: 'Engagement', body: rowData => threatLevelformat(rowData.ProfileEngagement_score) },
    // { field: 'timestamp', header: 'Last Post', body: rowData => formatRowDate(rowData.timestamp), minWidth: '250px' },
];


export const scammersRankingHeadersWatchList = [
    { field: 'rank', header: 'Rank', body:TextWithHash, style: { maxWidth: 20 }  },
    { field: 'user_handle', header: 'Name' ,body:AvatarWithText},
    { field: 'ProfileEngagement_score', header: 'Engagement', body:  rowData => threatLevelformat(rowData.ProfileEngagement_score), style: { width: '20%' } },
    { field: 'LatestVideoPostedDate', header: 'Last Post',body:PostDateUi },
    
];

export const scammersRankingData = [
    {
        id: 1,
        rank: '#1',
        name: 'Marvin McKinney',
        threatLevel: '90%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 2,
        rank: '#2',
        name: 'Annabel Rohan',
        threatLevel: '80%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 3,
        rank: '#3',
        name: 'Wade Warren',
        threatLevel: '70%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 4,
        rank: '#4',
        name: 'Tyra Dhillon',
        threatLevel: '60%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 5,
        rank: '#5',
        name: 'John Doe',
        threatLevel: '50%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 6,
        rank: '#6',
        name: 'Jane Doe',
        threatLevel: '40%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 7,
        rank: '#7',
        name: 'John Doe',
        threatLevel: '30%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 8,
        rank: '#8',
        name: 'Jane Doe',
        threatLevel: '20%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 9,
        rank: '#9',
        name: 'John Doe',
        threatLevel: '10%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 10,
        rank: '#10',
        name: 'Jane Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 11,
        rank: '#11',
        name: 'John Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 12,
        rank: '#12',
        name: 'Jane Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 13,
        rank: '#13',
        name: 'John Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 14,
        rank: '#14',
        name: 'Jane Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 15,
        rank: '#15',
        name: 'John Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 16,
        rank: '#16',
        name: 'Jane Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 17,
        rank: '#17',
        name: 'John Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 18,
        rank: '#18',
        name: 'Jane Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 19,
        rank: '#19',
        name: 'John Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    },
    {
        id: 20,
        rank: '#20',
        name: 'Jane Doe',
        threatLevel: '5%',
        avatarUrl:'https://primefaces.org/cdn/primereact/images/avatar/stephenshaw.png',
    }
    
 
]

// const processDateFormatter = (rowData) => {
//     const date = new Date(rowData.ss_process_timestamp);

//     const year = date.getFullYear();
//     const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-based
//     const day = String(date.getDate()).padStart(2, '0');
  
//     const hours = String(date.getHours()).padStart(2, '0');
//     const minutes = String(date.getMinutes()).padStart(2, '0');
  

//     const formattedDate = `${day}/${month}/${year} ${hours}:${minutes}`;
  
//     return formattedDate;
//   }

const processDateFormatter = (rowData) => {
    const date = new Date(rowData.ss_process_timestamp);

    // Add one day
    date.setDate(date.getDate() + 1);

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-based
    const day = String(date.getDate()).padStart(2, '0');
  
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
  
    const formattedDate = `${day}/${month}/${year} ${hours}:${minutes}`;
  
    return formattedDate;
}


export const contentListHeaders = [
    { field: 'identification_id', header: 'Case ID' },
    // { field: 'video_posted_timestamp', header: 'Date and Time', body: formatDate },
    { field: 'ss_process_timestamp', header: 'Date and Time', body: processDateFormatter },
    { field: 'video_source', header: 'Social Media' },
    { field: 'ai_topic', header: 'Topic'},
    // { field: 'status', header: 'Status of Content', body: formatStatus },
    { field: 'risk_status', header: 'Risk' , body: CustomBox},
];

export const aiAgentListHeaders = [
    { field: 'identification_id', header: 'Content ID' },
    { field: 'video_posted_timestamp', header: 'Date and Time', body: formatDate },
    { field: 'video_source', header: 'Social Media' },
    { field: 'video_source', header: 'Category' },
    { field: 'sub_category', header: 'Sub-Category' },
    { field: 'ai_topic', header: 'Topic'},
    // { field: 'status', header: 'Status of Content', body: formatStatus },
    { field: 'risk_status', header: 'Risk' , body: CustomBox},
];

export const archiveListHeaders = [
    { field: 'identification_id', header: 'ID Number' },
    { field: 'video_posted_timestamp', header: 'Date and Time', body: formatDate },
    { field: 'video_source', header: 'Social Media' },
    { field: 'category', header: 'Category'},
    { field: 'sub_category', header: 'Sub Category', },
    { field: 'ai_topic', header: 'Topic', },
    { field: 'status', header: 'Status' },
    { field: 'risk_status', header: 'Risk' , body: CustomBox},
];

export const contentListData = [
    {
        id: 'FB240228CBMM000021',
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 'FB240228CBMM000022',
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 'FB240228CBMM000023',
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 'FB240228CBMM000024',
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 'FB240228CBMM000025',
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 'FB240228CBMM000026',
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 'FB240228CBMM000027',
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 'FB240228CBMM000028',
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 9,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'High',
    },
    {
        id: 10,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 11,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 12,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 13,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 14,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 15,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 16,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 17,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 18,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 19,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Verified',
        risk: 'Medium',
    },
    {
        id: 20,
        time: '12/12/2021 12:00',
        socialMedia: 'Twitter',
        topic: 'Bitcoin',
        statusOfContent: 'Unverified',
        risk: 'Low',
    }

];

export const AiAgentListHeader = [
    { field: 'agentName', header: 'AI Agent Name' },
    { field: 'createdBy', header: 'Created by' },
    { field: 'createdTime', header: 'Created Time' },
    { field: 'validityPeriod', header: 'Validity Period' },
    { field: 'status', header: 'Status' },
]

export const AiAgentList=[
    {
        agentName:'AgentName1',
        agentID:1,
        category: "Scam",
        subcategory: "Cryptocurrency",
        createdBy:'Jayde Barney',
        createdTime:'1 Aug 2024',
        crawlingPeriod:'5 Jan 2023 - 5 Jan 2027',
        status:'Ready',
        totalContent: 7311122,
        isPublished: true,
    },
    {
        agentName:'AgentName2',
        agentID:2,
        category: "Scam",
        subcategory: "Cryptocurrency",
        createdBy:'Jayde Barney',
        createdTime:'1 Aug 2024',
        crawlingPeriod:'5 Jan 2023 - 5 Jan 2027',
        status:'Crawling',
        totalContent: 22,
        isPublished: false,
    },
    {
        agentName:'AgentName3',
        agentID:3,
        category: "Scam",
        subcategory: "Cryptocurrency",
        createdBy:'Jayde Barney',
        createdTime:'1 Aug 2024',
        crawlingPeriod:'5 Jan 2023 - 5 Jan 2027',
        status:'Reviewed',
        totalContent: 11122,
        isPublished: false,
    },
    {
        agentName:'AgentName4',
        agentID:4,
        category: "Scam",
        subcategory: "Cryptocurrency",
        createdBy:'Jayde Barney',
        createdTime:'1 Aug 2024',
        crawlingPeriod:'5 Jan 2023 - 5 Jan 2027',
        status: 'Crawling',
        totalContent: 0,
        isPublished: false,
    },
    {
        agentName:'AgentName5',
        agentID:5,
        category: "Scam",
        subcategory: "Cryptocurrency",
        createdBy:'Jayde Barney',
        createdTime:'1 Aug 2024',
        crawlingPeriod:'5 Jan 2023 - 5 Jan 2027',
        status: 'Ready',
        totalContent: 7311122,
        isPublished: true,
    },
    {
        agentName:'AgentName6',
        agentID:5,
        category: "Scam",
        subcategory: "Cryptocurrency",
        createdBy:'Razieh Abedi',
        createdTime:'1 Aug 2024',
        crawlingPeriod:'5 Jan 2023 - 5 Jan 2027',
        status: 'Ready',
        totalContent: 7311122,
        isPublished: false,
    }
]

function convertDate(dateStr) {
    // Parse the date string
    const date = new Date(dateStr);

    // Define month abbreviations
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    // Extract date components
    const day = String(date.getDate()).padStart(2, '0');
    const month = months[date.getMonth()];
    const year = String(date.getFullYear()).slice(-2);

    // Format the date
    return `${day} ${month} ${year}`;
};

function PostDateUi(rowData){
    const date = convertDate(rowData?.LatestVideoPostedDate)
    return <span>
{date}
    </span>
}