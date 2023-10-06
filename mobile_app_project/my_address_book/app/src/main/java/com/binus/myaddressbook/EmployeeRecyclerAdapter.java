package com.binus.myaddressbook;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.AsyncTask;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.RelativeLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;


import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;

public class EmployeeRecyclerAdapter extends RecyclerView.Adapter<EmployeeRecyclerAdapter.MyViewHolder> {
    private ArrayList<Employee> employeeList;

    public EmployeeRecyclerAdapter(ArrayList<Employee> employeeList) {
        this.employeeList = employeeList;
    }

    @NonNull
    @Override
    public MyViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View itemView = LayoutInflater.from(parent.getContext()).inflate(R.layout.employee_view, parent, false);
        return new MyViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(@NonNull EmployeeRecyclerAdapter.MyViewHolder holder, int position) {
        Picture photo_paths = employeeList.get(position).getPicture();
        String photo_path = photo_paths.getLarge();

        Integer employeeId = employeeList.get(position).getEmployeeId();

        Name names = employeeList.get(position).getName();
        String first_name = names.getFirst();
        String last_name = names.getLast();

        Registered registered = employeeList.get(position).getRegistered();
        String dateRegistered = registered.getDate();
        String[] datePart = dateRegistered.split("-");

        Calendar cal=Calendar.getInstance();
        SimpleDateFormat month_date = new SimpleDateFormat("MMMM");
        int monthnum = Integer.parseInt(datePart[1]);
        cal.set(Calendar.MONTH, monthnum);
        String month_name = month_date.format(cal.getTime());

        String city = employeeList.get(position).getLocation().getCity();
        String country = employeeList.get(position).getLocation().getCountry();
        String phone = employeeList.get(position).getPhone();
        String cell = employeeList.get(position).getCell();

        new DownloadImageFromInternet(holder.employee_photo).execute(photo_path);

        holder.name_text.setText(first_name + " " + last_name);
        holder.member_since_text.setText("Member since: " + month_name + " " + datePart[0]);
        holder.location_text.setText(city + ", " + country);
        holder.phone_text.setText(phone + " / " + cell);
    }

    @Override
    public int getItemCount() {
        return employeeList.size();
    }

    public class MyViewHolder extends RecyclerView.ViewHolder {
        private ImageView employee_photo;

        private TextView name_text;
        private TextView member_since_text;
        private TextView location_text;
        private TextView phone_text;

        private final Context context;

        public MyViewHolder (final View view) {
            super(view);
            this.name_text = view.findViewById(R.id.name_text);
            this.member_since_text = view.findViewById(R.id.member_since_text);
            this.location_text = view.findViewById(R.id.location_text);
            this.phone_text = view.findViewById(R.id.phone_text);
            this.employee_photo = view.findViewById(R.id.employee_photo);
            context = itemView.getContext();

            view.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    Employee employee = employeeList.get(getAdapterPosition());
                    Intent intent = new Intent(context, EmployeeDetailActivity.class)
                            .putExtra("employee_id", employee.getEmployeeId().toString());
                    context.startActivity(intent);
                }
            });
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
