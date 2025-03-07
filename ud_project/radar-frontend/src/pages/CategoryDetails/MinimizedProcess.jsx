import { ArrowRight } from "../../assets/icons";

const MinimizedProcess = ({ openDialog }) => {
    return (
        <div className="minimized-process">
            <span>Total Content: 1</span><span>Process: 0</span><span>Finish: 0</span><span>Error: 0</span>
            <img onClick={openDialog} src={ArrowRight} alt="Arrow right icon" />
        </div>
    )
}

export default MinimizedProcess;