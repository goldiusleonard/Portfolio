import React from 'react';
import styles from './HashTagRow.module.scss';


const HashTagRow = (props ) => {
    const lowCaseLevel = props.level?.toLowerCase();
    const onClick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (props.onClick) {
            props.onClick(props.item);
        }

    }

    return (
        <div className='keyword-containers' onClick={onClick}>
            <p className={styles['keyword-label']}>{'#' + props.item.name}</p>
            <div className={styles['risk-level'] + ' ' + styles[lowCaseLevel]} >
                {props.level}
            </div>

        </div>
    );
};

export default HashTagRow;
