import React from "react";
import { IconField } from "primereact/iconfield";
import { InputIcon } from "primereact/inputicon";
import { InputText } from "primereact/inputtext";
import 'primeicons/primeicons.css';

export default function Searchbar(props) {
    return (
        <IconField iconPosition="left" className="search-bar">
            <InputIcon className="pi pi-search"> </InputIcon>
            <InputText v-model="value1" placeholder="Search"  {...props} />
        </IconField>

    )
}
