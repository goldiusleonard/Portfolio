import React from 'react'
import RiskLevelLabel from '../RiskLevelLabel';
import NotRelatedIcon from '../../assets/icons/NotRelatedIcon.svg'
import RelatedIcon from '../../assets/icons/RelatedIcon.svg'
import data from '../../data/AiBuilderData/parameterList.json'

const AgentOutputParameters = () => {
    return (
        <div className='parameter-list-wrapper card-wrap'>
            <h2 className='title-type-2 p-3'>Parameter List</h2>
            <div className='list-wrapper'>
                <ul class="p-list">
                    { data.parameterList && data.parameterList.map((parameterItem, index) => (
                        <li key={index} className="p-list__item">
                            <div className='p-list__item_1'>
                                <div className="source-box">
                                    {parameterItem?.source}
                                </div>
                            </div>
                            <div className='p-list__item_2'>{parameterItem?.parameter}</div>
                            <div className='p-list__item_3'>
                                <RiskLevelLabel riskLevel={parameterItem?.riskLevel} />
                            </div>
                            <div className='p-list__item_4'>
                                <img src={parameterItem?.relatedStatus ? RelatedIcon : NotRelatedIcon} alt="Related Status" />
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    )
}

export default AgentOutputParameters
