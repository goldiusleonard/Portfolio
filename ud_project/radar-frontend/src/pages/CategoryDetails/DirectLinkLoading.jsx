import { Spinner } from "../../assets/icons"

const DirectLinkLoading = () => {
    return (
        <div className="direct-link-loading">
            <img src={Spinner} alt="Spinner icon" />
            <p>40%</p>
        </div>
    )
}

export default DirectLinkLoading