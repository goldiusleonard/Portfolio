import React, { useEffect, useMemo, useRef, useState } from "react";
import CustomModal from "../custom-modal/CustomModal";
import { CloseIcon } from "../../assets/icons";
import sample_profile_image from "../../assets/images/avatar.png";
import live_vidio from "../../assets/images/upin.png";
import facebookIcon from "../../assets/icons/facebookIcon.svg";
import Select from "../Select/Select";
import RealtimeChartCustom from "../charts/RealtimeChart/RealtimeChart";

const options1 = [
    "Choose a subject for your email template",
    "Report of Violent Threats",
    "Report of Copyright Theft",
    "Request for Investigation",
];
const options2 = [
    "Choose list organization who will receive this email",
    "Communication & Industry Relation (example@email.com)",
    "Regulatory Policy (example@email.com)",
    "Consumer & Industry Affair (example@email.com)",
];

const NotificationInfoUser = () => {
    return (
        <div className="header-user-live-detail">
            <div className="header-user-wrapper">
                <div className="header-user-image">
                    <img
                        src={sample_profile_image}
                        alt="notification-profile"
                    />
                    <div className="header-user-live">LIVE</div>
                </div>
                <div className="header-username">Jane Cooper</div>
            </div>
            <div className="header-user-detail">
                <div className="header-user-detail-item">
                    <h4>Following</h4>
                    <p className="user-detail-count">9M</p>
                </div>
                <div className="header-user-detail-item">
                    <h4>Followers</h4>
                    <p className="user-detail-count">908</p>
                </div>
                <div className="header-user-detail-item">
                    <h4>Post</h4>
                    <p className="user-detail-count">11.642</p>
                </div>
            </div>
        </div>
    );
};

const NotificationInfoSocmed = () => {
    return (
        <div className="header-info-socmed-detail">
            <div className="header-info-socmed-image-wrapper">
                <div className="header-info-socmed-image">
                    <img src={facebookIcon} alt="socmed-facebook" />
                    <div className="header-info-socmed-time">
                        <p>17:03</p>
                        <p>Oct 11, 2024</p>
                    </div>
                </div>
            </div>
            <div className="header-socmed-detail">
                <div className="header-socmed-detail-item">
                    <h4>Likes</h4>
                    <p className="user-detail-count">24.000</p>
                </div>
                <div className="header-socmed-detail-item">
                    <h4>Comments</h4>
                    <p className="user-detail-count">908</p>
                </div>
                <div className="header-socmed-detail-item">
                    <h4>Shares</h4>
                    <p className="user-detail-count">908</p>
                </div>
                <div className="header-socmed-detail-item">
                    <h4>Enggament</h4>
                    <p className="user-detail-count">11.642</p>
                </div>
            </div>
        </div>
    );
};

const NotificationLiveJustification = () => {
    const dataJustification = {
        en: `According to the video, there are strong indications that the content
        might be high likely a scam. This is suggested by the involvement of a
        person associated with OctaFX, a company already listed by Bank Negara
        Malaysia and Securities Commission Malaysia as an unauthorised entity.
        Additionally, the video promises high returns on investment for joining
        their group, a claim that appears suspiciously unrealistic. Furthermore,
        the lack c. Furthermore, the lack of c. Furthermore, the lack of c.
        Furthermore, the lack of c. Furthermore, the lack of of transparency is
        evident as Malaysia as an unauthorised entity. Additionally, the .`,
        my: `Menurut video itu, terdapat petunjuk kukuh bahawa
 kandungan berkemungkinan besar penipuan. Ini dicadangkan oleh
 penglibatan seseorang yang dikaitkan dengan OctaFX, sebuah syarikat
 telah disenaraikan oleh Bank Negara Malaysia dan Suruhanjaya Sekuriti
 Malaysia sebagai entiti yang tidak dibenarkan. Selain itu, video
 menjanjikan pulangan pelaburan yang tinggi kerana menyertai kumpulan mereka, a
 dakwaan yang kelihatan mencurigakan tidak realistik. Tambahan pula,
 kekurangan c. Tambahan pula, kekurangan c. Tambahan pula, kekurangan c.
 Tambahan pula, kekurangan c. Tambahan pula, kekurangan daripada
 ketelusan terbukti kerana Malaysia sebagai entiti yang tidak dibenarkan.
 Selain itu, .`,
    };

    const [languange, setLanguage] = useState("en");

    const handleLanguageChange = (language) => {
        setLanguage(language);
    };

    return (
        <div className="live-justification-wrapper">
            <div className="live-justification-header">
                <div className="live-justification-title">
                    Live Justification
                </div>
                <div className="live-justification-header-language">
                    <button
                        className={`${languange === "en" ? "active" : ""}`}
                        onClick={() => handleLanguageChange("en")}
                    >
                        English
                    </button>
                    <button
                        className={`${languange === "my" ? "active" : ""}`}
                        onClick={() => handleLanguageChange("my")}
                    >
                        Malaysia
                    </button>
                </div>
            </div>
            <div className="live-justification-content">
                {dataJustification[languange]}
            </div>
        </div>
    );
};

const NotificationLiveTranscripts = () => {
    return (
        <div className="live-transcript-wrapper">
            <div className="live-transcript-header">
                <div className="live-transcript-title">Live Transcript</div>
            </div>
            <div className="live-transcript-content">
                <p>
                    [00:30]
                    <br />
                    Mark (talking to himself, smiling):
                    <br />
                    "Just send the emails, tell them they’ve won. It’s easy
                    money. No one will ever suspect anything."
                </p>
                <p>
                    [00:45]
                    <br />
                    [Cut to a split screen: on one side, Mark continues typing
                    on his laptop; on the other side, we see a woman, Lisa,
                    reading the email on her phone.]
                </p>
                <p>
                    [01:00]
                    <br />
                    "'Congratulations, you've won $50,000! To claim your prize,
                    simply send a $500 fee to cover processing costs.' Hmm,
                    sounds too good to be true."
                </p>
                <p>
                    [01:15]
                    <br />
                    Mark (thinking to himself):
                    <br />
                    "This is going too well... They’ll start sending the money
                    soon. I’ll be rich in no time."
                </p>
                <p>
                    [01:30]
                    <br />
                    "I don’t know, it just feels a little off. Why would I have
                    to pay a fee to claim a prize? I think I’ll do a little
                    research."
                </p>
            </div>
        </div>
    );
};

const NotificationComments = () => {
    return (
        <div className="comments-wrapper">
            <div className="comments-header">
                <div className="comments-title">Comment’s Replies</div>
            </div>
            <div className="comments-content-wrapper">
                <div className="comments-content-item">
                    <div className="comments-content-user-item">
                        <img
                            src={sample_profile_image}
                            alt="user-profile"
                            className="comments-image"
                        />
                        <p>Made Waren</p>
                    </div>
                    <div className="comments-content">
                        "I think it's important to understand that these types
                        of scams are becoming more common. I'm not saying this
                        is the only scam, but it's certainly a growing concern."
                    </div>
                </div>
            </div>
        </div>
    );
};

const NotificationDetail = ({ isShowModal, handleModal }) => {
    const [statusForm, setStatusForm] = useState("hidden");

    const [selectedOptions1, setSelectedOptions1] = useState(options1[0]);
    const [selectedOptions2, setSelectedOptions2] = useState(options1[0]);

    const notificationDetailRef = useRef(null);

    const handleButtonSubmit = () => {
        if (statusForm === "hidden") {
            setStatusForm("show");
        }

        if (statusForm === "show") {
            handleCloseModal();
        }
    };

    const handleCloseModal = () => {
        setStatusForm("hidden");
        handleModal();
    };

    const handleSelectChange1 = (option) => {
        setSelectedOptions1(option);
    };
    const handleSelectChange2 = (option) => {
        setSelectedOptions2(option);
    };

    const titleContent = (
        <div className="title-content d-flex align-items-center justify-content-between w-100">
            Live Video Monitor
            <CloseIcon onClick={handleCloseModal} fill="#80EED3" />
        </div>
    );

    const isShowForm = useMemo(() => statusForm === "show", [statusForm]);

    const contentModal = (
        <div className="content-modal">
            <div className="modal-notification-content-wrapper">
                <div className="content-item-left">
                    <div
                        className={`content-live-vidio-wrapper ${
                            isShowForm && "small"
                        }`}
                    >
                        <img src={live_vidio} alt="live-vidio" />
                    </div>
                    <div className="content-live-chart-wrapper">
                        {/* <RealtimeChart height={isShowForm ? "129" : "135"} /> */}
                        <RealtimeChartCustom height={isShowForm ? 129 : 135} />
                    </div>
                </div>
                <div className="content-item-right">
                    <NotificationInfoUser />
                    <NotificationInfoSocmed />
                    <NotificationLiveJustification />
                    <NotificationLiveTranscripts />
                    <NotificationComments />
                </div>
            </div>
            <div
                className={`content-report ${
                    statusForm !== "hidden" ? "show" : "hide"
                }`}
            >
                <div className="content-report-header">
                    Send content report to External Organization (Optional)
                </div>
                <div className="content-report-form">
                    <div className="content-report-form-item">
                        <label
                            className="label-report-form"
                            htmlFor="content-report-name"
                        >
                            Report Subject
                        </label>
                        <Select
                            options={options1}
                            defaultValue={options1[0]}
                            onChange={handleSelectChange1}
                        />
                    </div>
                    <div className="content-report-form-item">
                        <label className="label-report-form">
                            Select Organization
                        </label>
                        <Select
                            options={options2}
                            defaultValue={options2[0]}
                            onChange={handleSelectChange2}
                        />
                    </div>
                    <div className="content-report-form-item">
                        <label className="label-report-form">
                            Send to custom email
                        </label>
                        <input
                            className="field-input-email"
                            type="text"
                            placeholder="Type list of email who will receive this email"
                        />
                    </div>
                </div>
            </div>
        </div>
    );

    const footerModal = (
        <div className="modal-notification-footer-buttons">
            <button className="close-button" onClick={handleCloseModal}>
                Close
            </button>
            <button className="report-live-button" onClick={handleButtonSubmit}>
                Report Live Vidio
            </button>
        </div>
    );

    const closeNotification = (event) => {
        if (
            notificationDetailRef.current &&
            !notificationDetailRef.current.contains(event.target)
        ) {
            handleCloseModal();
        }
    };

    useEffect(() => {
        document.addEventListener("mousedown", closeNotification);

        return () => {
            document.removeEventListener("mousedown", closeNotification);
        };
    }, []);

    return (
        <CustomModal
            ref={notificationDetailRef}
            isOpen={isShowModal}
            size={"xl"}
            className={"modal-notification-details-wrapper"}
            title={titleContent}
            content={contentModal}
            footer={footerModal}
        />
    );
};

export default NotificationDetail;
