import React from 'react';
import './News.scss';
import ArrowOutwardIcon from "../../assets/icons/ArrowOutwardIcon";
// import NewsLogoIcon from "../../assets/icons/NewsLogoIcon";
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import LoaderAnimation from '../LoaderAnimation';

import MalayMailWeb from "../../assets/NewsSource/malay_mail.svg";
import SaysWeb from "../../assets/NewsSource/Says.webp";
import TheStarWeb from "../../assets/NewsSource/the_star.png";
import HarianMetroWeb from "../../assets/NewsSource/harian_metro.png";
import MalaysiaKini from "../../assets/NewsSource/malaysia_kini.svg";
import TheRakyatWeb from "../../assets/NewsSource/the_rakyat_post.png";
import NewStraitsTimesWeb from "../../assets/NewsSource/new_straits_times.png";
import PrNews from "../../assets/NewsSource/PrNews.png";
import ChannelNews from "../../assets/NewsSource/ChannelNewsAsia.svg";
import moment from 'moment';


const News = ({ categories }) => {
    const { data, loadingData } = useApiData(
        `${endpoints.getNewsList}?${categories.map(v => `categories=${v}`).join('&')}`
    );

    const sourceNameToImage = (source) => {
        const imageMap = {
            "Malay Mail": MalayMailWeb,
            "Says": SaysWeb,
            "The Star": TheStarWeb,
            "Harian Metro": HarianMetroWeb,
            "Malaysia Kini": MalaysiaKini,
            "The Rakyat Post": TheRakyatWeb,
            "New Straits Times": NewStraitsTimesWeb,
            "prnewswire_apac": PrNews,
            "Channel News Asia": ChannelNews
        };

        const defaultImage = "default-image-url.jpg";

        const imageUrl = imageMap[source] || defaultImage;

        return imageUrl;
    };

    return (
        <>
            {loadingData ? <LoaderAnimation /> : <>
                <div className="news-container">
                    <div className="category-title">Related News ({data?.news?.length || 0})</div>
                    <div className='items-wrapper'>
                        {data ? data?.news?.map((item, index) => (
                            <div className="news-item" key={index} style={{ marginTop: index === 0 ? '0' : '12px' }}>
                                    <a target='_blank' href={item.link} className='wrap-anchor' rel="noreferrer">
                                        <div className='news-image'>
                                            {/* <NewsLogoIcon /> */}
                                            <img src={item.image} alt={item.sourceId} />
                                        </div>
                                        <div className="news-title">
                                            {item.title}
                                            <div className="news-source">{item.sourceId + " - " + moment(item.publishDate).format('D MMMM YYYY')}
                                                {/* <ArrowOutwardIcon /> */}
                                            </div>
                                        </div>
                                    </a>
                                </div>
                        )) :
                            <div className='text-center align-handle'>No news found</div>
                        }
                    </div>
                </div>

            </>}
        </>
    );
}

export default News;
