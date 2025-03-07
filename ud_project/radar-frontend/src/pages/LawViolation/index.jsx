import React, { useCallback, useEffect, useMemo, useState } from "react";
import Searchbar from "../../components/ui/inputs/Searchbar";
import LawViolationUploadModal from "../../components/Modal/LawViolationUploadModal";
import { PlusIcon } from "../../assets/icons";
import Button from "../../components/button/Button";
import TableLawReferences from "../../components/TableLawReferences";
import lawReferencesDataTable from "../../data/sampleJson/lawReferencesDataTable.json";
import ModalLawReferencesConfirmation from "../../components/Modal/ModalLawReferencesConfirmation";
import Alert from "../../components/Alert";
import useApiData from "../../hooks/useApiData";
import endpoints from "../../config/config.dev";
import moment from "moment";
import axios from "axios"
import { getUserFromLocalStorage } from '../../Util';

const initialAlert = {
  show: '',
  type: '',
  message: ''
}

const LawViolation = () => {
  const user = getUserFromLocalStorage()
  const token = user?.access_token

  const { data: categoriesData } = useApiData(endpoints.category)
  const { data: lawViolations, loadingData: loadingLawViolations, refetch: refetchLawViolations } = useApiData(
    endpoints.getLawViolations
  );
  const [isShowModal, setIsShowModal] = useState(false);
  const [isShowModalConfirmation, setIsShowModalConfirmation] = useState(false);
  const [modalConfirmationType, setModalConfirmationType] = useState("created");
  const [selectedData, setSelectedData] = useState(undefined);
  const [searchValue, setSearchValue] = useState("");
  const [alert, setAlert] = useState(initialAlert);
  const { refetch: deleteLawViolationFile } = useApiData(
    `${endpoints.deleteLawViolationFile}/${selectedData?.id || 0}`,
    'DELETE',
    {
      enabled: false
    }
  );
  const { data: lawViolationDetail, loadingData: loadingLawViolationDetail, refetch: refetchLawViolationDetail } = useApiData(
    `${endpoints.getLawViolationDetail}/${selectedData?.id || 0}`,
    'GET',
    {
      enabled: false
    }
  );
  const [loadingSubmit, setLoadingSubmit] = useState(false)

  useEffect(() => {
    if (selectedData) {
      refetchLawViolationDetail()
    }
  }, [selectedData])

  const handleFilterChangeTable = (event) => {
    setSearchValue(event.target.value);
  };

  const handleShowModalUpload = () => {
    if (!isShowModal) setSelectedData(undefined);
    setIsShowModal((prevState) => !prevState);
  };

  const handleShowEditLawReference = (data) => {
    setSelectedData(data);
    setIsShowModal((prevState) => !prevState);
  };

  const handleIsShowModalConfirmation = (type) => {
    if (!isShowModalConfirmation) handleShowModalUpload();
    setIsShowModalConfirmation((prevState) => !prevState);

    if (type === "delete") {
      setAlert(initialAlert);
      return setModalConfirmationType("delete");
    }
    if (type === "updated") return setModalConfirmationType("updated");
    if (type === "created") return setModalConfirmationType("created");
    return;
  };

  const postFile = async (payload) => {
    try {
      setLoadingSubmit(true)
      const formData = new FormData()
      formData.append('law_file', payload.file)
      formData.append('law_name', payload.lawName)
      formData.append('category', payload.lawCategory)
      formData.append('effective_date', moment(payload.lawEffectiveDate).format('MM-DD-YYYY'))
      formData.append('publisher', payload.lawPublisher)
      formData.append('summary', payload.lawSummary || '')

      const res = await axios.post(endpoints.postLawViolationFile, formData, {
        headers: {
          accept: 'application/json',
          Authorization: `Bearer ${token}`,
        }
      })

      if (res.data.error) throw new Error(res.data.message)

      handleIsShowModalConfirmation("created")
      refetchLawViolations()
    } catch (ex) {
      return setAlert({
        show: true,
        message: ex,
        type: 'fail'
      });
    } finally {
      setLoadingSubmit(false)
    }
  }

  const putLawViolation = async (payload) => {
    try {
      setLoadingSubmit(true)

      const data = {
        law_name: payload.lawName,
        category: payload.lawCategory,
        effective_date: moment(payload.lawEffectiveDate).format('MM-DD-YYYY'),
        upload_date: moment(selectedData.upload_date).format('MM-DD-YYYY'),
        publisher: payload.lawPublisher,
        summary: payload.lawSummary || ''
      }

      const res = await axios.put(`${endpoints.editLawViolationFile}/${selectedData?.id}`, data, {
        headers: {
          accept: 'application/json',
          Authorization: `Bearer ${token}`,
        }
      })

      if (res.data.error) throw new Error(res.data.message)

      handleIsShowModalConfirmation("updated")
      refetchLawViolations()
    } catch (ex) {
      return setAlert({
        show: true,
        message: ex,
        type: 'fail'
      });
    } finally {
      setLoadingSubmit(false)
    }
  }

  const handleConfrimationAction = async () => {
    if (modalConfirmationType === "delete") {
      await deleteLawViolationFile()
      refetchLawViolations()
      setAlert({
        show: true,
        message: 'Law Deleted Successfully!',
        type: 'success'
      });
      return handleIsShowModalConfirmation();
    }
  };

  const filterLawViolations = useMemo(
    () => {
      if (loadingLawViolations) return []

      return lawViolations.data.filter((data) =>
        data.name.toLowerCase().includes(searchValue.toLowerCase())
      ).map(data => ({
        ...data,
        effective_date: moment(data.effective_date).format('YYYY-MM-DD'),
        upload_date: moment(data.upload_date).format('YYYY-MM-DD')
      }))
    },
    [loadingLawViolations, lawViolations, searchValue]
  );

  const alertComponent = useMemo(
    () => (
      <Alert
        message={alert.message}
        info={alert.type}
        duration={2000}
        visible={alert.show}
      />
    ),
    [alert]
  );

  const onSubmitData = (payload) => {
    if (selectedData) {
      putLawViolation(payload)
    } else {
      postFile(payload)
    }
  }

  const categoriesOptionsMemo = useMemo(() => {
    if (!categoriesData) return []

    return categoriesData.categories.map(v => v.name)
  }, [categoriesData])

  const renderUploadModal = useCallback(() => {
    if (isShowModal && selectedData && !lawViolationDetail) return null

    return (
      <LawViolationUploadModal
        isShowModal={isShowModal}
        handleCloseModal={handleShowModalUpload}
        categories={categoriesOptionsMemo}
        isEdit={!!selectedData}
        editData={lawViolationDetail?.data}
        onDelete={() => handleIsShowModalConfirmation("delete")}
        onSubmit={onSubmitData}
        isLoading={loadingSubmit}
      />
    )
  }, [isShowModal, selectedData, lawViolationDetail, loadingSubmit])

  return (
    <div className="wrapper-law-violation">
      <div className="wrapped-law-violation-header d-flex gap-3">
        <Searchbar
          placeholder="Search Keyword"
          onChange={(event) => handleFilterChangeTable(event)}
        />
        <Button
          onClick={handleShowModalUpload}
          className="outline"
          text={
            <div className="d-flex align-items-center gap-3">
              <PlusIcon fill="#fff" />
              Upload New Law
            </div>
          }
        />
      </div>
      <div className="law-references-table-wrapper">
        <TableLawReferences
          loading={loadingLawViolations}
          data={filterLawViolations}
          onRowClick={handleShowEditLawReference}
          onAddNewLaw={handleShowModalUpload}
        />
        {alertComponent}
      </div>

      <ModalLawReferencesConfirmation
        type={modalConfirmationType}
        isOpen={isShowModalConfirmation}
        onClose={handleIsShowModalConfirmation}
        onAction={handleConfrimationAction}
      />

      {renderUploadModal()}
    </div>
  );
};

export default LawViolation;
