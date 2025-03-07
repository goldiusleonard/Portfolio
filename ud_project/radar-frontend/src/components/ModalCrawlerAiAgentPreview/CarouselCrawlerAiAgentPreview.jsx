import React from 'react'
import { Swiper, SwiperSlide } from 'swiper/react'
import { Pagination, EffectCoverflow, Navigation } from 'swiper/modules'
import "swiper/css";
import "swiper/css/effect-coverflow";
import "swiper/css/pagination";
import iconChevronLeft from '../../assets/icons/chevron-left.svg'
import iconChevronRight from '../../assets/icons/chevron-right.svg'

//Props 
// {
//   images: [] of url
// }

const CarouselCrawlerAiAgentPreview = ({
  images
}) => {
  return (
    <Swiper
      effect="coverflow"
      grabCursor
      centeredSlides
      slidesPerView="auto"
      coverflowEffect={{
        rotate: 0,
        stretch: 0,
        depth: 100,
        modifier: 7,
        slideShadows: true,
      }}
      modules={[EffectCoverflow, Pagination, Navigation]}
      navigation={{
        nextEl: ".btn-carousel-next",
        prevEl: ".btn-carousel-prev",
      }}
      className="doc-swiper cards"
    >
      <button
        className="btn-carousel btn-carousel-prev"
      >
        <img src={iconChevronLeft} alt="Prev" />
      </button>
      <button
        className="btn-carousel btn-carousel-next"
      >
        <img src={iconChevronRight} alt="Next" />

      </button>
      {images.map((v, idx) => (
        <SwiperSlide
          key={idx}
        >
          <div
            key={idx}
            className="carousel-card"
          >
            <img
              className="content"
              src={v}
              alt="Crawler AI Agent Builder" />
          </div>
        </SwiperSlide>
      ))}
    </Swiper>
  )
}

export default CarouselCrawlerAiAgentPreview