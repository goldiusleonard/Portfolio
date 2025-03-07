export default function formatNumber(value, currencySymbol = '$') {
  function formatSingleNumber(number, divisor, suffix) {
    return (
      (number / divisor).toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 1
      }).replace(/(\.00)+$/, '') +
      suffix
    );
  }

  function formatNumberBasedOnRange(number) {
    if (Math.abs(number) >= 1e9) {
      return formatSingleNumber(number, 1e9, 'B');
    } else if (Math.abs(number) >= 1e6) {
      return formatSingleNumber(number, 1e6, 'M');
    } else if (Math.abs(number) >= 1e3) {
      return formatSingleNumber(number, 1e3, 'K');
    } else {
      return number.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 1
      }).replace(/(\.00)+$/, '');
    }
  }

  if (typeof value === 'number') {
    return formatNumberBasedOnRange(value);
  }

  if (Array.isArray(value)) {
    return value.map((item) => formatNumberBasedOnRange(Number(item)));
  }

  if (typeof value === 'string' && !Number.isNaN(parseFloat(value))) {
    return formatNumberBasedOnRange(parseFloat(value));
  }

  return value;
}