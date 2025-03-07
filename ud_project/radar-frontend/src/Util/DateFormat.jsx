import moment from "moment";

export const formatRowDate = (timestamp) => {
    return moment(timestamp).format('DD MMM YY');
};