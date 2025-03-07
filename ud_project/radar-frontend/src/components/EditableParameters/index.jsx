import React, { useState } from 'react'
import RiskLevelLabel from '../RiskLevelLabel';
import editIcon from '../../assets/icons/pen.svg';
import deleteIcon from '../../assets/icons/bin.svg';
import './EditableParameters.scss'

const ParameterList = [
    {
        parameter: 'Inviting users to click a URL link',
        riskLevel: 'high',
        tag: 'AI',
        source: 'TiktokVideo_2783628738.mkv'
    },
    {
        parameter: 'High promising words',
        riskLevel: 'low',
        tag: 'V1',
        source: 'TiktokVideo_2783628738.mkv'
    },
    {
        parameter: 'Requests for personal information',
        riskLevel: 'medium',
        tag: 'v2',
        source: 'TiktokVideo_2783628738.mkv'
    },
    {
        parameter: 'Unsolicited investment offers',
        riskLevel: 'medium',
        tag: 'AI',
        source: 'TiktokVideo_2783628738.mkv'
    },
    {
        parameter: 'Guaranteed high returns',
        riskLevel: 'low',
        tag: 'V3',
        source: 'TiktokVideo_2783628738.mkv'
    },
    {
        parameter: 'Anonymous or untraceable transactions',
        riskLevel: 'high',
        tag: 'V1',
        source: 'TiktokVideo_2783628738.mkv'
    },
    {
        parameter: 'Phishing emails or messages',
        riskLevel: 'high',
        tag: 'AI',
        source: 'TiktokVideo_2783628738.mkv'
    }
]

const EditableParameters = () => {
    return (
        <div className='parameter-list-wrapper editable-parameters parameter card-wrap'>
            <div className='list-wrapper'>
                <ul className="p-list">
                    {ParameterList && ParameterList.map((parameterItem, index) => (
                        <li key={index} className="p-list__item">
                            <div className='p-list__item_1 toggle-action'>
                                <div className="form-check form-switch">
                                    <input
                                        className="form-check-input"
                                        type="checkbox"
                                        id={`flexSwitchCheckDefault-${index}`}
                                    />
                                    <label
                                        className="form-check-label"
                                        htmlFor={`flexSwitchCheckDefault-${index}`}
                                    ></label>
                                </div>
                            </div>
                            <div className='p-list__item_2 tag-icon tag'>{parameterItem?.tag}</div>
                            <div className='p-list__item_3 tag-icon'>{parameterItem?.parameter}</div>
                            <div className='p-list__item_4 risk-level'>
                                <RiskLevelLabel riskLevel={parameterItem?.riskLevel} />
                            </div>
                            <div className='p-list__item_5'>
                                <img src={editIcon} alt='edit icon' />
                                <img src={deleteIcon} alt='delete icon' />
                            </div>
                        </li>
                    ))}

                </ul>
            </div>
        </div>
    )
}

export default EditableParameters
