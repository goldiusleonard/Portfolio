import { LinechartIcon, HeatmapIcon } from '../../../assets/icons'

const ToggleChart = ({ active, onClick }) => {
    return (
        <div className='toggle-container'>
            <button onClick={onClick} name='heatmap' className={active === 'isHeatMap' ? 'active' : ''}>
                <HeatmapIcon fill={active === 'isHeatMap' ? 'rgba(255, 255, 255, 1)' : 'rgba(255, 255, 255, 0.4)'} />
            </button>
            <button onClick={onClick} name='lineChart' className={active === 'isLineChart' ? 'active' : ''}>
                <LinechartIcon fill={active === 'isLineChart' ? 'rgba(255, 255, 255, 1)' : 'rgba(255, 255, 255, 0.4)'} />
            </button>
        </div>
    )
}

export default ToggleChart;