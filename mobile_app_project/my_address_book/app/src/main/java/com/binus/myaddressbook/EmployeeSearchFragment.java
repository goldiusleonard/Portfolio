package com.binus.myaddressbook;

import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.Locale;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class EmployeeSearchFragment extends Fragment {
    private View view;
    private RecyclerView employee_list;
    private TextView no_employee_textview;
    private EditText search_box;
    private ImageButton search_btn;

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        view = inflater.inflate(R.layout.fragment_employee_search, container, false);
        employee_list = view.findViewById(R.id.employee_list);
        no_employee_textview = view.findViewById(R.id.no_employee_text);
        search_box = view.findViewById(R.id.employee_search_edit_text);
        search_btn = view.findViewById(R.id.employee_search_search_btn);

        search_btn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                filter(search_box.getText().toString());
            }
        });

        search_box.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {

            }

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {

            }

            @Override
            public void afterTextChanged(Editable s) {
                if(s.toString().isEmpty()) {
                    filter(s.toString());
                }
            }
        });

        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl("https://u73olh7vwg.execute-api.ap-northeast-2.amazonaws.com/")
                .addConverterFactory(GsonConverterFactory.create())
                .build();

        JSONPlaceholder jsonPlaceholder = retrofit.create(JSONPlaceholder.class);
        Call<resModel> call = jsonPlaceholder.getEmployees();
        call.enqueue(new Callback<resModel>() {
            @Override
            public void onResponse(Call<resModel> call, Response<resModel> response) {
                if(!response.isSuccessful()) {
                    Toast.makeText(EmployeeSearchFragment.this.getContext(), response.code(), Toast.LENGTH_SHORT).show();
                    return;
                }
                ArrayList<Employee> employeeList = response.body().getEmployees();

                EmployeeRecyclerAdapter adapter = new EmployeeRecyclerAdapter(employeeList);
                RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(view.getContext());
                employee_list.setLayoutManager(layoutManager);
                employee_list.setItemAnimator(new DefaultItemAnimator());
                employee_list.setAdapter(adapter);

                if (adapter.getItemCount() == 0) {
                    no_employee_textview.setVisibility(View.VISIBLE);
                    employee_list.setVisibility(View.GONE);
                }
                else {
                    no_employee_textview.setVisibility(View.GONE);
                    employee_list.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onFailure(Call<resModel> call, Throwable t) {
                Toast.makeText(EmployeeSearchFragment.this.getContext(), t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
        return view;
    }

    private void filter(String searchText) {
        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl("https://u73olh7vwg.execute-api.ap-northeast-2.amazonaws.com/")
                .addConverterFactory(GsonConverterFactory.create())
                .build();

        JSONPlaceholder jsonPlaceholder = retrofit.create(JSONPlaceholder.class);
        Call<resModel> call = jsonPlaceholder.getEmployees();
        call.enqueue(new Callback<resModel>() {
            @Override
            public void onResponse(Call<resModel> call, Response<resModel> response) {
                if(!response.isSuccessful()) {
                    Toast.makeText(EmployeeSearchFragment.this.getContext(), response.code(), Toast.LENGTH_SHORT).show();
                    return;
                }
                ArrayList<Employee> employeeList = response.body().getEmployees();
                ArrayList<Employee> filteredList = new ArrayList<>();

                for (Employee employee : employeeList) {
                    String name = employee.getName().getFirst().toLowerCase() + " " + employee.getName().getLast().toLowerCase();
                    if (name.contains(searchText.toLowerCase())) {
                        filteredList.add(employee);
                    }
                }

                EmployeeRecyclerAdapter adapter = new EmployeeRecyclerAdapter(filteredList);
                RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(view.getContext());
                employee_list.setLayoutManager(layoutManager);
                employee_list.setItemAnimator(new DefaultItemAnimator());
                employee_list.setAdapter(adapter);

                if (adapter.getItemCount() == 0) {
                    no_employee_textview.setVisibility(View.VISIBLE);
                    employee_list.setVisibility(View.GONE);
                }
                else {
                    no_employee_textview.setVisibility(View.GONE);
                    employee_list.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onFailure(Call<resModel> call, Throwable t) {
                Toast.makeText(EmployeeSearchFragment.this.getContext(), t.getMessage(), Toast.LENGTH_SHORT).show();
                Log.i("ngetes", "masuk sini");
            }
        });
    }
}