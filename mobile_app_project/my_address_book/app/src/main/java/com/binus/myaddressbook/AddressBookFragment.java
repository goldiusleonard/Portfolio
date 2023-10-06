package com.binus.myaddressbook;

import android.database.Cursor;
import android.media.Image;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.DefaultItemAnimator;
import androidx.recyclerview.widget.ItemTouchHelper;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class AddressBookFragment extends Fragment {
    private View view;
    private RecyclerView address_book_list;
    private TextView no_address_book_textview;
    private DBHelper dbHelper;
    private ArrayList<AddressBook> addressBooksList;
    private AddressBookRecyclerAdapter adapter;
    private ImageButton search_btn;
    private EditText search_box;

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container,
                             Bundle savedInstanceState) {

        view = inflater.inflate(R.layout.fragment_address_book, container, false);
        address_book_list = view.findViewById(R.id.address_book_list);
        no_address_book_textview = view.findViewById(R.id.no_address_book_text);
        dbHelper = new DBHelper(view.getContext());
        search_box = view.findViewById(R.id.address_book_edit_text);
        search_btn = view.findViewById(R.id.address_book_search_btn);

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

        Cursor res = dbHelper.getData();
        addressBooksList = new ArrayList<>();
        while(res.moveToNext()) {
            addressBooksList.add(new AddressBook(res.getString(0),
                    res.getString(1),
                    res.getString(2),
                    res.getString(3),
                    res.getString(4),
                    res.getString(5),
                    res.getString(6),
                    res.getString(7),
                    res.getString(8)));
        }

        adapter = new AddressBookRecyclerAdapter(addressBooksList);
        RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(view.getContext());
        address_book_list.setLayoutManager(layoutManager);
        address_book_list.setItemAnimator(new DefaultItemAnimator());
        address_book_list.setAdapter(adapter);
        new ItemTouchHelper(itemTouchHelperCallback).attachToRecyclerView(address_book_list);

        if (addressBooksList.size() == 0) {
            no_address_book_textview.setVisibility(View.VISIBLE);
            address_book_list.setVisibility(View.GONE);
        }
        else {
            no_address_book_textview.setVisibility(View.GONE);
            address_book_list.setVisibility(View.VISIBLE);
        }

        return view;
    }

    ItemTouchHelper.SimpleCallback itemTouchHelperCallback = new ItemTouchHelper.SimpleCallback(0, ItemTouchHelper.RIGHT | ItemTouchHelper.LEFT) {
        @Override
        public boolean onMove(@NonNull RecyclerView recyclerView, @NonNull RecyclerView.ViewHolder viewHolder, @NonNull RecyclerView.ViewHolder target) {
            return false;
        }

        @Override
        public void onSwiped(@NonNull RecyclerView.ViewHolder viewHolder, int direction) {
            AddressBook item = addressBooksList.get(viewHolder.getAdapterPosition());
            dbHelper.deleteData(item.getId());
            addressBooksList.remove(viewHolder.getAdapterPosition());
            adapter.notifyDataSetChanged();
            if (addressBooksList.size() == 0) {
                no_address_book_textview.setVisibility(View.VISIBLE);
                address_book_list.setVisibility(View.GONE);
            }
            else {
                no_address_book_textview.setVisibility(View.GONE);
                address_book_list.setVisibility(View.VISIBLE);
            }
        }
    };

    private void filter(String searchText) {
        Cursor res = dbHelper.getData();
        addressBooksList = new ArrayList<>();
        while(res.moveToNext()) {
            String name = res.getString(1).toLowerCase() + " " + res.getString(2).toLowerCase();
            if (name.contains(searchText.toLowerCase())) {
                addressBooksList.add(new AddressBook(res.getString(0),
                        res.getString(1),
                        res.getString(2),
                        res.getString(3),
                        res.getString(4),
                        res.getString(5),
                        res.getString(6),
                        res.getString(7),
                        res.getString(8)));
            }
        }

        adapter = new AddressBookRecyclerAdapter(addressBooksList);
        RecyclerView.LayoutManager layoutManager = new LinearLayoutManager(view.getContext());
        address_book_list.setLayoutManager(layoutManager);
        address_book_list.setItemAnimator(new DefaultItemAnimator());
        address_book_list.setAdapter(adapter);
        new ItemTouchHelper(itemTouchHelperCallback).attachToRecyclerView(address_book_list);

        if (addressBooksList.size() == 0) {
            no_address_book_textview.setVisibility(View.VISIBLE);
            address_book_list.setVisibility(View.GONE);
        }
        else {
            no_address_book_textview.setVisibility(View.GONE);
            address_book_list.setVisibility(View.VISIBLE);
        }
    }
}