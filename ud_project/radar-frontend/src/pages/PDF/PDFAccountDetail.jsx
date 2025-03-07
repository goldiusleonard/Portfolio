import React, { useState } from "react";
import PDFAccountDetailUserInfo from "../../components/PDF/PDFAccountDetailUserInfo";
import HeatMap from "../../components/HeatMap";
import { useLocation } from "react-router-dom";
import creatorData from "../CreatorScreen/CreatorScreen.json";
import { SingleLinechart } from "../../components";
import CategoryPostStatus from "../CreatorScreen/CategoryPostStatus";
import useApiData from "../../hooks/useApiData";
import endpoints from "../../config/config.dev";
import CreatorDO from "../../components/CreatorDO";
import PDFAccountDetailThread from "../../components/PDF/PDFAccountDetailThread";

const datas = [
    {
        threadDate: "Wed, 27 Apr",
        threadDatas: [
            {
                category: "Scam",
                content:
                    "Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience. These scams not only crush the hopes of young job seekers but also exploit their desperation. It's frustrating to see the job market flooded with such dishonesty. These scams waste time and often result in financial losses. When will these fraudulent practices end?Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience. These scams not only crush the hopes of young job seekers but also exploit their desperation. It's frustrating to see the job market flooded with such dishonesty. These scams waste time and often result in financial losses. When will these fraudulent practices end?",
                urlLink: "https://vm.tiktok.com/ZMMgSefg5/",
                categoryType: "High",
            },
            {
                category: "Scam",
                content:
                    "Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience. These scams not only crush the hopes of young job seekers but also exploit their desperation. It's frustrating to see the job market flooded with such dishonesty. These scams waste time and often result in financial losses. When will these fraudulent practices end?Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience.",
                urlLink: "https://vm.tiktok.com/ZMMgSefg5/",
                categoryType: "Medium",
            },
            {
                category: "Scam",
                content:
                    "Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience. These scams not only crush the hopes of young job seekers but also exploit their desperation. It's frustrating to see the job market flooded with such dishonesty. ",
                urlLink: "https://vm.tiktok.com/ZMMgSefg5/",
                categoryType: "Low",
            },
        ],
    },
    {
        threadDate: "Wed, 28 Apr",
        threadDatas: [
            {
                category: "Scam",
                content:
                    "Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience. These scams not only crush the hopes of young job seekers but also exploit their desperation. It's frustrating to see the job market flooded with such dishonesty. These scams waste time and often result in financial losses. When will these fraudulent practices end?Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience. These scams not only crush the hopes of young job seekers but also exploit their desperation. It's frustrating to see the job market flooded with such dishonesty. These scams waste time and often result in financial losses. When will these fraudulent practices end?",
                urlLink: "https://vm.tiktok.com/ZMMgSefg5/",
                categoryType: "High",
            },
            {
                category: "Scam",
                content:
                    "Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience. These scams not only crush the hopes of young job seekers but also exploit their desperation. It's frustrating to see the job market flooded with such dishonesty. These scams waste time and often result in financial losses. When will these fraudulent practices end?Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience.",
                urlLink: "https://vm.tiktok.com/ZMMgSefg5/",
                categoryType: "Medium",
            },
            {
                category: "Scam",
                content:
                    "Fresh graduates in Malaysia are being deceived by false job postings claiming RM10,000 monthly salaries without experience. These scams not only crush the hopes of young job seekers but also exploit their desperation. It's frustrating to see the job market flooded with such dishonesty. ",
                urlLink: "https://vm.tiktok.com/ZMMgSefg5/",
                categoryType: "Low",
            },
        ],
    },
];

const PDFAccountDetail = () => {
    const location = useLocation();

    const [highlightedContent, setHighlightedContent] = useState([]);
    const [year, setYear] = useState("2024");
    const [date, setDate] = useState(null);
    const [isHeatmap, setIsHeatmap] = useState(true);
    const lineChartRef = React.useRef();

    const {
        profile_id: id,
        user_handle: name,
        engagementDate,
    } = location.state ? location.state : [];

    const apiEndpoint = `${endpoints.getCreatorProfile}?userName=${name}`;
    const { data: creatorProfileData } = useApiData(apiEndpoint);

    const handleDateSelect = React.useCallback((e) => {
        setDate(e);
    }, []);

    const handleHighlightedContent = (content) => {
        setHighlightedContent(content);
    };

    const handleToggle = (e) => {
        setIsHeatmap(e.currentTarget.name === "heatmap");
    };

    const widthLineChart = lineChartRef.current?.offsetWidth;

    return (
        <div className="pdf-account-details">
            <PDFAccountDetailUserInfo />
            <div
                className="card-wrap pdf-account-details-heatmap"
                ref={lineChartRef}
            >
                {isHeatmap ? (
                    <HeatMap
                        data={creatorData.profiles[0].threats}
                        setHighlightedContent={handleHighlightedContent}
                        engagementDate={engagementDate}
                        profileName={name}
                        year={year}
                        setDate={handleDateSelect}
                        handleToggle={handleToggle}
                    />
                ) : (
                    <SingleLinechart
                        width={widthLineChart}
                        setDate={handleDateSelect}
                        handleToggle={handleToggle}
                        creatorName={name}
                        handleHighlightedContent={handleHighlightedContent}
                    />
                )}
            </div>
            <div className="pdf-account-detail-enggament-wrapper">
                <CategoryPostStatus
                    data={[
                        { title: "Scam", value: 10000 },
                        { title: "Hate Speech", value: 7200 },
                        { title: "3R", value: 5900 },
                        { title: "Category #1", value: 712 },
                        { title: "Category #2", value: 712 },
                        { title: "Category #3", value: 712 },
                        { title: "Category #4", value: 712 },
                    ]}
                    maxProgress={10000}
                    minHigh={8000}
                    minMedium={5000}
                    progressLabelFormatter={(v) => {
                        console.log(v);
                        if (v >= 1000) return `${v / 1000}k`;
                        return v;
                    }}
                />
                <div className="data-observatory card-wrap">
                    <h5>Top Similiar Creator</h5>
                    {creatorProfileData && (
                        <CreatorDO
                            creatorName={creatorProfileData[0]?.user_handle}
                        />
                    )}
                </div>
            </div>

            <PDFAccountDetailThread listThread={datas} />
        </div>
    );
};

export default PDFAccountDetail;
