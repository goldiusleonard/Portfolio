import React, { useRef, useEffect, useState } from 'react';
import { Messages } from 'primereact/messages';
// import './Alert.scss';

const Alert = ({ message, info, duration = 4000, visible = true }) => {
    const msgs = useRef(null);
    const [show, setShow] = useState(visible ? 'flex' : 'none');

    useEffect(() => {
        if (visible && msgs.current) {
            msgs.current.clear();
            msgs.current.show([
                { severity: info, detail: message, sticky: true, closable: false }
            ]);
            setShow('flex');
            const timer = setTimeout(() => {
                msgs.current.clear();
                setShow('none');
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [message, info, duration, visible]);

    return (
        <div className="alert" style={{ display: show }}>
            <Messages className={info === 'fail' ? 'message danger' : 'message'} ref={msgs} />
        </div>
    );
};

export default Alert;
