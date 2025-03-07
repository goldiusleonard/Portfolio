import React, { useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import NavBar from '../NavBar'
import TopHeader from '../TopHeader'
import { useReactToPrint } from "react-to-print";
import { useRef } from "react";

function AppLayout() {
    const navigate = useNavigate();
    const location = useLocation();

    const contentRef = useRef(null);
    const reactToPrintFn = useReactToPrint({ contentRef });

    useEffect(() => {
        if (location.pathname === '/') {
            navigate('/login');
        }
    }, [navigate, location.pathname]);

    return (
        <div className='main-layout'>
            {!location.pathname.includes('pdf') && <NavBar />}
            {!location.pathname.includes('pdf') && <div className='page-container'>
                <TopHeader />
                <div className='content-wrapper'>
                    <Outlet />
                </div>
            </div>}
            {location.pathname.includes('pdf') && <button onClick={() => reactToPrintFn()}>Print</button>}
            {location.pathname.includes('pdf') && <div ref={contentRef} className='pdf-container'>
                <Outlet />
            </div>}
        </div>
    )
}

export default AppLayout