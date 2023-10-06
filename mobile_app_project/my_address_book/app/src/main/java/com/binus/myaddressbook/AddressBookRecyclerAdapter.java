package com.binus.myaddressbook;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.AsyncTask;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;

public class AddressBookRecyclerAdapter extends RecyclerView.Adapter<AddressBookRecyclerAdapter.MyViewHolder> {
    private ArrayList<AddressBook> addressBookList;

    public AddressBookRecyclerAdapter(ArrayList<AddressBook> addressBookList) {
        this.addressBookList = addressBookList;
    }

    @NonNull
    @Override
    public AddressBookRecyclerAdapter.MyViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View itemView = LayoutInflater.from(parent.getContext()).inflate(R.layout.address_book_view, parent, false);
        return new AddressBookRecyclerAdapter.MyViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(@NonNull AddressBookRecyclerAdapter.MyViewHolder holder, int position) {
        String first = addressBookList.get(position).getFirst();
        String last = addressBookList.get(position).getLast();
        String city = addressBookList.get(position).getCity();
        String country = addressBookList.get(position).getCountry();
        String phone = addressBookList.get(position).getPhone();
        String email = addressBookList.get(position).getEmail();
        String photo_path = addressBookList.get(position).getImage_path();

        holder.name_text.setText(first + " " + last);
        holder.location_text.setText(city + ", " + country);

        new AddressBookRecyclerAdapter.DownloadImageFromInternet(holder.employee_photo).execute(photo_path);

        holder.call_button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + phone));
                v.getContext().startActivity(intent);
            }
        });

        holder.email_button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent emailIntent = new Intent(Intent.ACTION_SENDTO, Uri.parse("mailto:" + email));
                v.getContext().startActivity(Intent.createChooser(emailIntent, "Choose the email app"));
            }
        });
    }

    @Override
    public int getItemCount() {
        return addressBookList.size();
    }

    public class MyViewHolder extends RecyclerView.ViewHolder {
        private ImageView employee_photo;

        private TextView name_text;
        private TextView location_text;
        private Button call_button;
        private Button email_button;

        public MyViewHolder (final View view) {
            super(view);
            this.name_text = view.findViewById(R.id.address_book_name_text);
            this.location_text = view.findViewById(R.id.address_book_location_text);
            this.employee_photo = view.findViewById(R.id.address_book_photo);
            this.call_button = view.findViewById(R.id.call_button);
            this.email_button = view.findViewById(R.id.email_button);
        }

    }

    private class DownloadImageFromInternet extends AsyncTask<String, Void, Bitmap> {
        ImageView imageView;

        public DownloadImageFromInternet(ImageView imageView) {
            this.imageView = imageView;
        }

        protected Bitmap doInBackground(String... urls) {
            String imageURL = urls[0];
            Bitmap bimage = null;
            try {
                InputStream in = new java.net.URL(imageURL).openStream();
                bimage = BitmapFactory.decodeStream(in);

            } catch (Exception e) {
                Log.e("Error Message", e.getMessage());
                e.printStackTrace();
            }
            return bimage;
        }

        protected void onPostExecute(Bitmap result) {
            imageView.setImageBitmap(result);
        }
    }

}
